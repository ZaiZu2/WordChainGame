import asyncio
from datetime import datetime, timedelta
from enum import Enum
from logging import getLogger
from typing import Any, Callable, Iterable, Mapping, cast

from fastapi import WebSocket, WebSocketDisconnect, WebSocketException
from sqlalchemy import and_, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

import src.schemas.database as db
import src.schemas.domain as d
import src.schemas.validation as v
from config import get_config
from src.connection_manager import ConnectionManager
from src.database import init_db_session
from src.game.deathmatch import Deathmatch
from src.game.game import GameManager
from src.misc import PlayerAlreadyConnectedError


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
    message: db.Message,
    player: d.Player,
    db: AsyncSession,
    conn_manager: ConnectionManager,
) -> None:
    db.add(message)
    await db.flush([message])
    await db.refresh(message, attribute_names=['player'])

    chat_message = v.Message(
        id_=message.id_,
        player_name=message.player.name,
        room_id=message.room_id,
        content=message.content,
        created_on=message.created_on,
    )
    await conn_manager.send_chat_message(chat_message, player.id_)


async def save_and_broadcast_message(
    message: db.Message, db: AsyncSession, conn_manager: ConnectionManager
) -> None:
    db.add(message)
    await db.flush([message])
    await db.refresh(message, attribute_names=['player'])

    chat_message = v.Message(
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
    db_session: AsyncSession,
    conn_manager: ConnectionManager,
    leave_message: str | None = None,
) -> None:
    """
    Move the player from the old room to the new one and broadcast the change in
    corresponding chats.
    """
    conn_manager.move_player(player.id_, from_room_id, to_room_id)

    message = db.Message(
        content=leave_message or f'{player.name} left the room',
        room_id=from_room_id,
        player_id=d.ROOT.id_,
    )
    await save_and_broadcast_message(message, db_session, conn_manager)

    message = db.Message(
        content=f'{player.name} joined the room',
        room_id=to_room_id,
        player_id=d.ROOT.id_,
    )
    await save_and_broadcast_message(message, db_session, conn_manager)

    # TODO: Add RoomState websocket message as well?
    # TODO: Add LobbyState websocket message if lobby is involved?


async def accept_websocket_connection(
    player: d.Player,
    websocket: WebSocket,
    db_session: AsyncSession,
    conn_manager: ConnectionManager,
) -> None:
    await websocket.accept()

    try:
        conn_manager.connect(player, d.LOBBY.id_)
    except PlayerAlreadyConnectedError:
        exc_args = (
            v.CustomWebsocketCodeEnum.MULTIPLE_CLIENTS,
            'Player is already connected with another client.',
        )
        # Send a message to the duplicate client, then terminate the connection
        await conn_manager.send_connection_state(*exc_args, websocket)

        # Inform the original client about the connection attempt
        room_id_with_logged_player = conn_manager.pool.get_room(
            player_id=player.id_
        ).id_
        message = db.Message(
            content='Someone tried to log into your account from another device',
            room_id=room_id_with_logged_player,
            player_id=d.ROOT.id_,
        )
        await save_and_send_message(message, player, db_session, conn_manager)
        raise WebSocketException(*exc_args) from None

    message = db.Message(
        content=f'{player.name} joined the room',
        room_id=d.LOBBY.id_,
        player_id=d.ROOT.id_,
    )
    await save_and_broadcast_message(message, db_session, conn_manager)


async def handle_player_disconnect(
    player: d.Player,
    db_session: AsyncSession,
    conn_manager: ConnectionManager,
) -> None:
    room = conn_manager.pool.get_room(player_id=player.id_)
    conn_manager.disconnect(player.id_)

    is_player_in_lobby = room.id_ == d.LOBBY.id_
    if not is_player_in_lobby:
        pass

        # TODO: Rewrite without db operations
        # if not active_game_with_player:
        #     # If disconnected while in a game room, throw the player into the lobby
        #     # player.room_id = d.LOBBY.id_
        #     # db.add(player)
        #     # await db.flush([player])
        #     room = await db_session.scalar(
        #         select(db.Room)
        #         .where(db.Room.id_ == room_id)
        #         .options(joinedload(db.Room.owner))
        #     )
        #     room_state = v.RoomState(
        #         **room.to_dict(),
        #         owner_name=room.owner.name,
        #         players={player.name: None},
        #     )
        #     await conn_manager.broadcast_room_state(room.id_, room_state)

        #     message = db.Message(
        #         content=f'{player.name} disconnected from the room',
        #         room_id=room.id_,
        #         player_id=d.ROOT.id_,
        #     )
        #     await save_and_broadcast_message(message, db_session, conn_manager)
        #     return
        # else:
        #     # TODO: If disconnected during the game, keep him in a room and the game for
        #     # a time being - to be decided
        #     pass
    else:
        lobby_state = v.LobbyState(
            players={player.name: None}, stats=get_current_stats(conn_manager)
        )
        await conn_manager.broadcast_lobby_state(lobby_state)

        message = db.Message(
            content=f'{player.name} disconnected from the room',
            room_id=room.id_,
            player_id=d.ROOT.id_,
        )
        await save_and_broadcast_message(message, db_session, conn_manager)


async def listen_for_messages(
    player: d.Player,
    db_session: AsyncSession,
    conn_manager: ConnectionManager,
    game_manager: GameManager,
):
    """Listen and distribute websocket messages to different handlers."""
    while True:
        try:
            # TODO: Make a wrapper which deserializes the websocket message when it arrives
            websocket_message_dict = await player.websocket.receive_json()
            websocket_message = v.WebSocketMessage(**websocket_message_dict)

            match type(websocket_message.payload):
                case v.Message:
                    chat_message = cast(v.Message, websocket_message.payload)
                    message = db.Message(
                        content=chat_message.content,
                        room_id=chat_message.room_id,
                        player_id=player.id_,
                    )
                    await save_and_broadcast_message(message, db_session, conn_manager)
                    await db_session.commit()
                case v.WordInput:
                    game_input = cast(v.WordInput, websocket_message.payload)
                    game = game_manager.get(game_input.game_id)

                    if game is None or game.players.current.id_ != player.id_:
                        continue  # TODO: Handle malicious attempts to send game input

                    room_id = conn_manager.pool.get_room(player_id=player.id_).id_
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


async def run_game(
    game: Deathmatch, room: d.Room, conn_manager: ConnectionManager
) -> None:
    start_game_state = game.start()
    await conn_manager.broadcast_game_state(room.id_, start_game_state)

    wait_state = game.wait()
    await conn_manager.broadcast_game_state(room.id_, wait_state)
    await asyncio.sleep(get_config().GAME_START_DELAY)

    while True:
        start_turn_state = game.start_turn()
        await conn_manager.broadcast_game_state(room.id_, start_turn_state)

        try:
            word_input = await asyncio.wait_for(
                room.word_input_buffer.get(), game.time_left_in_turn
            )
        except asyncio.TimeoutError:
            end_turn_state = game.end_turn_timed_out()
        else:
            end_turn_state = game.end_turn_in_time(word_input.word)
        await conn_manager.broadcast_game_state(room.id_, end_turn_state)
        await consume_game_events(game, conn_manager)

        if game.is_finished():
            break

        wait_state = game.wait()
        await conn_manager.broadcast_game_state(room.id_, wait_state)
        await asyncio.sleep(get_config().TURN_START_DELAY)

    end_game_state = game.end()
    await consume_game_events(game, conn_manager)
    await conn_manager.broadcast_game_state(room.id_, end_game_state)

    room.status = d.RoomStatusEnum.OPEN
    await broadcast_single_room_state(room, conn_manager)

    await export_and_persist_game(game)


async def broadcast_full_lobby_state(
    conn_manager: ConnectionManager,
    removed_player_names: Iterable[str] | None = None,
    removed_room_ids: Iterable[int] | None = None,
) -> None:
    lobby_players = conn_manager.pool.get_room_players(d.LOBBY.id_)
    # Merge the players and the removed players to create a full state update
    players_out = {
        **{
            lobby_player.name: v.LobbyPlayerOut.model_validate(lobby_player)
            for lobby_player in lobby_players
        },
        **{player_name: None for player_name in removed_player_names or []},
    }

    # Merge the rooms and the removed rooms to create a full state update
    rooms_out = {
        **{
            room.id_: v.RoomOut(
                players_no=len(room.players),
                owner_name=room.owner.name,
                **room.to_dict(),
            )
            for room in conn_manager.pool.get_rooms()
        },
        **{room_id: None for room_id in removed_room_ids or []},
    }
    lobby_state = v.LobbyState(
        rooms=rooms_out, players=players_out, stats=get_current_stats(conn_manager)
    )
    await conn_manager.broadcast_lobby_state(lobby_state)


async def export_and_persist_game(game: Deathmatch) -> None:
    """Gather game data designated to be persisted and issue a bulk insert."""
    async with init_db_session() as db_session:
        game_db = cast(
            db.Game,
            await db_session.scalar(select(db.Game).where(db.Game.id_ == game.id_)),
        )
        game_db.ended_on = datetime.utcnow()
        game_db.status = db.GameStatusEnum.ENDED
        db_session.add(game_db)

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
        await db_session.execute(insert(db.Turn), turn_db_dicts)


async def broadcast_single_room_state(
    room: d.Room, conn_manager: ConnectionManager
) -> None:
    """Send `LobbyState` and `RoomState` broadcast for a single room state change."""
    room_players = conn_manager.pool.get_room_players(room.id_)
    room_state = v.RoomState(
        **room.to_dict(),
        players={room_player.name: room_player for room_player in room_players},  # type: ignore
        owner_name=room.owner.name,
    )
    await conn_manager.broadcast_room_state(room.id_, room_state)

    room_out = v.RoomOut(
        players_no=len(conn_manager.pool.get_room_players(room.id_)),
        owner_name=room.owner.name,
        **room.to_dict(),
    )
    lobby_state = v.LobbyState(
        rooms={room.id_: room_out}, stats=get_current_stats(conn_manager)
    )
    await conn_manager.broadcast_lobby_state(lobby_state)


def get_current_stats(conn_manager: ConnectionManager) -> v.CurrentStatistics:
    return v.CurrentStatistics(
        active_players=conn_manager.pool.active_players,
        active_rooms=conn_manager.pool.active_rooms,
    )


async def expire_inactive_rooms(conn_manager: ConnectionManager):
    async with init_db_session() as db_session:
        db_rooms = await db_session.scalars(
            select(db.Room).where(
                and_(db.Room.ended_on == None, db.Room.id_ != d.LOBBY.id_)  # noqa: E711
            )
        )

        current_date = datetime.utcnow()
        expired_rooms = []
        for db_room in db_rooms:
            try:
                room = conn_manager.pool.get_room(room_id=db_room.id_)
            except KeyError:
                # If the room is no longer in the pool, it probably means it was lost
                # due to a server crash or other error. It should be marked as finished
                # in the DB.
                db_room.ended_on = current_date
                db_session.add(db_room)
                expired_rooms.append(db_room.id_)
                continue

            time_since_last_active = (current_date - room.last_active_on).seconds
            if (
                not room.players
                and time_since_last_active > get_config().ROOM_DELETION_DELAY
            ):
                conn_manager.pool.remove_room(room.id_)
                db_room.ended_on = current_date
                db_session.add(db_room)
                expired_rooms.append(db_room.id_)

        await db_session.commit()
        await broadcast_full_lobby_state(conn_manager, removed_room_ids=expired_rooms)

        logger = getLogger('uvicorn')
        if len(expired_rooms) > 0:
            logger.info(f'RECURRING ROOM CLEANUP: Expired {len(expired_rooms)} rooms')
        else:
            logger.info('RECURRING ROOM CLEANUP: No rooms expired')


def schedule_recurring_task(
    started_on: datetime,
    interval: int,
    coro_func: Callable,
    args: Iterable[Any] | None = None,
    kwargs: Mapping[str, Any] | None = None,
):
    """
    Schedule a recurring task to be executed at a fixed interval from a start time. This
    avoids the drift in the execution time due to the time taken by the coroutine
    function.
    """
    args = args or []
    kwargs = kwargs or {}

    async def _recurring_task():
        last_scheduled_on = started_on
        while True:
            current_time = datetime.utcnow()
            time_diff = (current_time - last_scheduled_on).total_seconds()
            interval_count_since_last_execution = time_diff // interval
            time_until_next_run = interval - time_diff % interval

            last_scheduled_on += timedelta(
                seconds=interval_count_since_last_execution * interval
            )

            logger = getLogger('uvicorn')
            logger.debug(
                f'Executing recurring "{coro_func.__name__}", started on {started_on} every {interval}s\n'
                f'Current time: {current_time}\n'
                f'Last scheduled on: {last_scheduled_on}\n'
                f'Waiting for: {time_until_next_run}\n'
            )
            await asyncio.sleep(time_until_next_run)

            # Execute only if time difference is divisible by the polling interval with a 1
            # second upper tolerance.
            if time_diff % interval < 1:
                await coro_func(*args, **kwargs)

    return asyncio.create_task(_recurring_task())


async def consume_game_events(
    game: Deathmatch, conn_manager: ConnectionManager
) -> None:
    async with init_db_session() as db_session:
        for event in game.events:
            if isinstance(event, d.PlayerLostEvent):
                message = db.Message(
                    content=f'{event.player_name} lost the game',
                    room_id=game.room_id,
                    player_id=d.ROOT.id_,
                )
                await save_and_broadcast_message(message, db_session, conn_manager)
            elif isinstance(event, d.PlayerWonEvent):
                message = db.Message(
                    content=f'{event.player_name} won the game',
                    room_id=game.room_id,
                    player_id=d.ROOT.id_,
                )
                await save_and_broadcast_message(message, db_session, conn_manager)
            elif isinstance(event, d.GameFinishedEvent):
                message = db.Message(
                    content=f'game has finished - you created a word chain consisting of {event.chain_length} words',
                    room_id=game.room_id,
                    player_id=d.ROOT.id_,
                )
                await save_and_broadcast_message(message, db_session, conn_manager)
            else:
                raise NotImplementedError('Unsupported event type')
