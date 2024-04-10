from enum import Enum
from typing import cast

from fastapi import WebSocket, WebSocketException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

import src.models as d  # d - database
import src.schemas as s  # s - schema
from src.connection_manager import ConnectionManager
from src.game import GameManager


class TagsEnum(str, Enum):
    ALL = 'all'


tags_metadata = [
    {
        'name': TagsEnum.ALL,
        'description': 'All routes',
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
    did_connect = conn_manager.connect(player.id_, d.LOBBY.id_, websocket)
    if not did_connect:
        exc_args = [
            s.CustomWebsocketCodeEnum.MULTIPLE_CLIENTS,
            'Player is already connected with another client.',
        ]
        # Send a message to the duplicate client, then terminate the connection
        await conn_manager.send_connection_state(*exc_args, websocket)

        # Inform the original client about the connection attempt
        _, room_id_with_already_logged_player = conn_manager.find_connection(player.id_)
        message = d.Message(
            content='Someone tried to log into your account from another device',
            room_id=room_id_with_already_logged_player,
            player_id=d.ROOT.id_,
        )
        await save_and_send_message(message, player, db, conn_manager)
        raise WebSocketException(*exc_args)

    message = d.Message(
        content=f'{player.name} joined the room',
        room_id=d.LOBBY.id_,
        player_id=d.ROOT.id_,
    )
    await save_and_broadcast_message(message, db, conn_manager)


async def handle_player_disconnect(
    player: d.Player,
    websocket: WebSocket,
    db: AsyncSession,
    conn_manager: ConnectionManager,
) -> None:
    await db.refresh(player)
    _, room_id = conn_manager.find_connection(player.id_)
    conn_manager.disconnect(player.id_, room_id, websocket)

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
    while True:
        # TODO: Make a wrapper which deserializes the websocket message when it arrives
        websocket_message_dict = await websocket.receive_json()
        websocket_message = s.WebSocketMessage(**websocket_message_dict)

        await db.refresh(player)
        match websocket_message.type:
            # TODO: Make a wrapper which handles CHAT type websocket messages
            case s.WebSocketMessageTypeEnum.CHAT:
                chat_message = cast(s.ChatMessage, websocket_message.payload)
                message = d.Message(
                    content=chat_message.content,
                    room_id=chat_message.room_id,
                    player=player,
                )
                await save_and_broadcast_message(message, db, conn_manager)
            case s.WebSocketMessageTypeEnum.GAME_INPUT:
                game_input = cast(s.GameInput, websocket_message.payload)
                game = game_manager.get(game_input.game_id)
                # TODO: Input data validation?
                turn_result = game.process_turn(game_input.word)
                game_state = s.GameState(
                    id_=game.id_,
                    status=game.status,
                    players=game.players,
                    lost_players=game.lost_players,
                    rules=game.rules,
                    current_turn=s.Turn(
                        current_player_idx=game.players.current_idx,
                        **game.current_turn.to_dict(),
                    ),
                )
                _, room_id = conn_manager.find_connection(player.id_)
                await conn_manager.broadcast_game_state(room_id, game_state)

        # Commit all flushed resources to DB every time a message is received
        await db.commit()


async def broadcast_full_lobby_state(
    db: AsyncSession, conn_manager: ConnectionManager
) -> None:
    player_ids = [conn.player_id for conn in conn_manager.connections[d.LOBBY.id_]]
    room_players = await db.scalars(
        select(d.Player).where(d.Player.id_.in_(player_ids))
    )
    players_out_map = {
        room_player.name: s.LobbyPlayerOut(**room_player.to_dict())
        for room_player in room_players
    }

    rooms = await db.scalars(
        select(d.Room)
        .where(d.Room.status != d.RoomStatusEnum.EXPIRED)
        .options(joinedload(d.Room.owner))
    )
    rooms_out_map = {
        room.id_: s.RoomOut(
            players_no=len(conn_manager.connections[room.id_]),
            owner_name=room.owner.name,
            **room.to_dict(),
        )
        for room in rooms
    }

    stats = s.CurrentStatistics(
        active_players=sum(len(conn) for conn in conn_manager.connections.values()),
        active_rooms=len(conn_manager.connections) - 1,  # exclude the Lobby
    )

    lobby_state = s.LobbyState(
        rooms=rooms_out_map, players=players_out_map, stats=stats
    )
    await conn_manager.broadcast_lobby_state(lobby_state)
