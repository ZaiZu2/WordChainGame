import asyncio
from datetime import datetime
from enum import Enum
from typing import cast

from fastapi import WebSocket, WebSocketDisconnect, WebSocketException
from sqlalchemy import and_, insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

import src.models as d  # d - database
import src.schemas as s  # s - schema
from config import get_config
from src.connection_manager import ConnectionManager
from src.dependencies import init_db_session
from src.error_handlers import PlayerAlreadyConnectedError
from src.game.deathmatch import Deathmatch
from src.game.game import GameManager


class TagsEnum(str, Enum):
    MAIN = 'main'
    ROOMS = 'rooms'


tags_metadata = [
    {
        'name': TagsEnum.MAIN,
        'description': 'General purpose routes',
    },
    {
        'name': TagsEnum.ROOMS,
        'description': 'Room-related routes',
    },
]


async def save_and_send_message(
    message: d.Message,
    player: d.Player,
    db: AsyncSession,
    conn_manager: ConnectionManager,
) -> None:
    db.add(message)
    await db.flush([message])
    await db.refresh(message, attribute_names=['player'])

    chat_message = s.ChatMessage(
        id_=message.id_,
        player_name=message.player.name,
        room_id=message.room_id,
        content=message.content,
        created_on=message.created_on,
    )
    await conn_manager.send_chat_message(chat_message, player.id_)


async def save_and_broadcast_message(
    message: d.Message, db: AsyncSession, conn_manager: ConnectionManager
) -> None:
    db.add(message)
    await db.flush([message])
    await db.refresh(message, attribute_names=['player'])

    chat_message = s.ChatMessage(
        id_=message.id_,
        player_name=message.player.name,
        room_id=message.room_id,
        content=message.content,
        created_on=message.created_on,
    )
    await conn_manager.broadcast_chat_message(chat_message)


async def move_player_and_broadcast_message(
    player: d.Player,
    from_room_id: int,
    to_room_id: int,
    db: AsyncSession,
    conn_manager: ConnectionManager,
) -> None:
    """
    Move the player from the old room to the new one and broadcast the change in
    corresponding chats.
    """
    conn_manager.move_player(player.id_, from_room_id, to_room_id)

    message = d.Message(
        content=f'{player.name} left the room',
        room_id=from_room_id,
        player_id=d.ROOT.id_,
    )
    await save_and_broadcast_message(message, db, conn_manager)

    message = d.Message(
        content=f'{player.name} joined the room',
        room_id=to_room_id,
        player_id=d.ROOT.id_,
    )
    await save_and_broadcast_message(message, db, conn_manager)


async def accept_websocket_connection(
    player: d.Player,
    websocket: WebSocket,
    db: AsyncSession,
    conn_manager: ConnectionManager,
) -> None:
    await websocket.accept()

    try:
        conn_manager.connect(player.id_, d.LOBBY.id_, websocket)
    except PlayerAlreadyConnectedError:
        exc_args = (
            s.CustomWebsocketCodeEnum.MULTIPLE_CLIENTS,
            'Player is already connected with another client.',
        )
        # Send a message to the duplicate client, then terminate the connection
        await conn_manager.send_connection_state(*exc_args, websocket)

        # Inform the original client about the connection attempt
        room_id_with_logged_player = conn_manager.pool.get_room(
            player_id=player.id_
        ).room_id
        message = d.Message(
            content='Someone tried to log into your account from another device',
            room_id=room_id_with_logged_player,
            player_id=d.ROOT.id_,
        )
        await save_and_send_message(message, player, db, conn_manager)
        raise WebSocketException(*exc_args) from None

    message = d.Message(
        content=f'{player.name} joined the room',
        room_id=d.LOBBY.id_,
        player_id=d.ROOT.id_,
    )
    await save_and_broadcast_message(message, db, conn_manager)


async def handle_player_disconnect(
    player: d.Player,
    db: AsyncSession,
    conn_manager: ConnectionManager,
) -> None:
    await db.refresh(player)
    room_id = conn_manager.pool.get_room(player_id=player.id_).room_id
    conn_manager.disconnect(player.id_)

    is_player_in_lobby = room_id == d.LOBBY.id_
    if not is_player_in_lobby:
        active_game_with_player = await db.scalar(
            select(d.Game).where(
                and_(
                    d.Game.status == d.GameStatusEnum.IN_PROGRESS,
                    d.Game.players.contains(player),
                )
            )
        )

        if not active_game_with_player:
            # If disconnected while in a game room, throw the player into the lobby
            # player.room_id = d.LOBBY.id_
            # db.add(player)
            # await db.flush([player])
            room = await db.scalar(
                select(d.Room)
                .where(d.Room.id_ == room_id)
                .options(joinedload(d.Room.owner))
            )
            room_state = s.RoomState(
                **room.to_dict(),
                owner_name=room.owner.name,
                players={player.name: None},
            )
            await conn_manager.broadcast_room_state(room_id, room_state)

            message = d.Message(
                content=f'{player.name} disconnected from the room',
                room_id=room_id,
                player_id=d.ROOT.id_,
            )
            await save_and_broadcast_message(message, db, conn_manager)
            return
        else:
            # TODO: If disconnected during the game, keep him in a room and the game for
            # a time being - to be decided
            pass
    else:
        # If disconnected while in the lobby, do nothing
        pass

        message = d.Message(
            content=f'{player.name} disconnected from the room',
            room_id=room_id,
            player_id=d.ROOT.id_,
        )
        await save_and_broadcast_message(message, db, conn_manager)


async def listen_for_messages(
    player: d.Player,
    websocket: WebSocket,
    db: AsyncSession,
    conn_manager: ConnectionManager,
    game_manager: GameManager,
):
    """Listen and distribute websocket messages to different handlers."""
    while True:
        try:
            # TODO: Make a wrapper which deserializes the websocket message when it arrives
            websocket_message_dict = await websocket.receive_json()
            websocket_message = s.WebSocketMessage(**websocket_message_dict)

            await db.refresh(player)
            match type(websocket_message.payload):
                case s.ChatMessage:
                    chat_message = cast(s.ChatMessage, websocket_message.payload)
                    message = d.Message(
                        content=chat_message.content,
                        room_id=chat_message.room_id,
                        player=player,
                    )
                    await save_and_broadcast_message(message, db, conn_manager)

                case s.WordInput:
                    game_input = cast(s.WordInput, websocket_message.payload)
                    game = game_manager.get(game_input.game_id)

                    if game is None or game.players.current.id_ != player.id_:
                        continue  # TODO: Handle malicious attempts to send game input

                    room_id = conn_manager.pool.get_room(player_id=player.id_).room_id
                    word_input_buffer = conn_manager.pool.get_room(
                        room_id=room_id
                    ).word_input_buffer
                    await word_input_buffer.put(game_input)

        except WebSocketDisconnect:
            raise
        except Exception as e:
            # TODO: Figure out a proper way to handle exceptions to avoid websocket
            # channel crashes
            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            print(e)

        # Commit all flushed resources to DB every time a message is received
        await db.commit()


async def run_game(
    game: Deathmatch, room_id: int, conn_manager: ConnectionManager
) -> None:
    word_input_queue = conn_manager.pool.get_room(room_id=room_id).word_input_buffer

    start_game_state = game.start()
    await conn_manager.broadcast_game_state(room_id, start_game_state)

    wait_state = game.wait()
    await conn_manager.broadcast_game_state(room_id, wait_state)
    await asyncio.sleep(get_config().GAME_START_DELAY)

    while True:
        start_turn_state = game.start_turn()
        await conn_manager.broadcast_game_state(room_id, start_turn_state)

        try:
            word_input = await asyncio.wait_for(
                word_input_queue.get(), game.time_left_in_turn
            )
        except asyncio.TimeoutError:
            end_turn_state = game.end_turn_timed_out()
        else:
            end_turn_state = game.end_turn_in_time(word_input.word)
        await conn_manager.broadcast_game_state(room_id, end_turn_state)

        if game.is_finished():
            break

        wait_state = game.wait()
        await conn_manager.broadcast_game_state(room_id, wait_state)
        await asyncio.sleep(get_config().TURN_START_DELAY)

    end_game_state = game.end()
    await conn_manager.broadcast_game_state(room_id, end_game_state)

    # TODO: Do i really want to store transient room changes in the DB?
    # Ideally, Room should store it's state in memory only
    async with init_db_session() as db:
        await export_and_persist_game(game, db)
        room = cast(
            d.Room,
            await db.scalar(
                select(d.Room)
                .where(d.Room.id_ == room_id)
                .options(joinedload(d.Room.owner))
            ),
        )
        await db.refresh(room)
        room.status = d.RoomStatusEnum.OPEN
        await broadcast_single_room_state(room, conn_manager)


async def broadcast_full_lobby_state(
    db: AsyncSession, conn_manager: ConnectionManager
) -> None:
    lobby_conns = conn_manager.pool.get_room_conns(d.LOBBY.id_)
    player_ids = [conn.player_id for conn in lobby_conns]
    room_players = await db.scalars(
        select(d.Player).where(d.Player.id_.in_(player_ids))
    )
    players_out = {
        room_player.name: s.LobbyPlayerOut(**room_player.to_dict())
        for room_player in room_players
    }

    rooms = await db.scalars(
        select(d.Room)
        .where(
            and_(d.Room.status != d.RoomStatusEnum.EXPIRED, d.Room.id_ != d.LOBBY.id_)
        )
        .options(joinedload(d.Room.owner))
    )
    rooms_out = {
        room.id_: s.RoomOut(
            players_no=len(lobby_conns),
            owner_name=room.owner.name,
            **room.to_dict(),
        )
        for room in rooms
    }

    stats = s.CurrentStatistics(
        active_players=conn_manager.pool.active_players,
        active_rooms=conn_manager.pool.active_rooms,
    )

    lobby_state = s.LobbyState(rooms=rooms_out, players=players_out, stats=stats)
    await conn_manager.broadcast_lobby_state(lobby_state)


async def export_and_persist_game(game: Deathmatch, db: AsyncSession) -> None:
    """Gather game data designated to be persisted and issue a bulk insert."""
    game_db = await db.scalar(select(d.Game).where(d.Game.id_ == game.id_))
    game_db.ended_on = datetime.utcnow()
    game_db.status = d.GameStatusEnum.FINISHED
    db.add(game_db)

    turn_db_dicts = []
    for turn in game.turns:
        turn_db_dict = dict(
            word=turn.word.content if turn.word else None,
            is_correct=turn.word.is_correct if turn.word else None,
            started_on=turn.started_on,
            ended_on=turn.ended_on,
            player_id=turn.player_id,
            game_id=game.id_,
        )
        turn_db_dicts.append(turn_db_dict)

    # Bulk insert
    await db.execute(insert(d.Turn), turn_db_dicts)


async def broadcast_single_room_state(
    room: d.Room, conn_manager: ConnectionManager
) -> None:
    """Send `LobbyState` and `RoomState` broadcast for a single room state change."""
    room_state = s.RoomState(**room.to_dict(), owner_name=room.owner.name)
    await conn_manager.broadcast_room_state(room.id_, room_state)

    room_out = s.RoomOut(
        players_no=len(conn_manager.pool.get_room_conns(room.id_)),
        owner_name=room.owner.name,
        **room.to_dict(),
    )
    lobby_state = s.LobbyState(rooms={room.id_: room_out})
    await conn_manager.broadcast_lobby_state(lobby_state)
