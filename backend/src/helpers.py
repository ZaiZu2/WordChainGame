from enum import Enum

from fastapi import WebSocket, WebSocketException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

import src.models as d  # d - database
import src.schemas as s  # s - schema
from src.connection_manager import ConnectionManager


class TagsEnum(str, Enum):
    ALL = 'all'


tags_metadata = [
    {
        'name': TagsEnum.ALL,
        'description': 'All routes',
    },
]


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


async def accept_websocket_connection(
    player: d.Player,
    websocket: WebSocket,
    db: AsyncSession,
    conn_manager: ConnectionManager,
) -> None:
    await websocket.accept()
    did_connect = conn_manager.connect(player.id_, player.room_id, websocket)
    if not did_connect:
        exc_args = [
            s.CustomWebsocketCodeEnum.MULTIPLE_CLIENTS,
            'Player is already connected with another client.',
        ]
        # Send a message to the duplicate client, then terminate the connection
        await conn_manager.send_connection_state(*exc_args, websocket)

        # Inform the original client about the connection attempt
        message = d.Message(
            content='Someone tried to log into your account from another device. If it was not you, please regenerate your account code.',
            room_id=player.room_id,
            player_id=d.ROOT.id_,
        )
        await save_and_broadcast_message(message, db, conn_manager)
        raise WebSocketException(
            *exc_args, 'Player is already connected with another client'
        )

    message = d.Message(
        content=f'{player.name} joined the room',
        room_id=player.room_id,
        player_id=d.ROOT.id_,
    )
    await save_and_broadcast_message(message, db, conn_manager)


async def send_initial_state(
    player: d.Player, db: AsyncSession, conn_manager: ConnectionManager
):
    """
    Send room specific state upon player's connection. If the player is in the lobby,
    send the lobby state. If a game in which player is participating is still on,
    reconnect him to that room.
    """
    # 1. TODO: Check and reconnect if the player was disconnected from any on-going game
    # room = db.scalar(
    #     select(d.Game)
    #     .join(d.Player, d.Game.players)
    #     .where(
    #         and_(
    #             d.Player.room_id == player.room_id,
    #             d.Game.status == d.GameStatusEnum.IN_PROGRESS,
    #         )
    #     )
    # )

    # 2. Send the lobby state
    result = await db.execute(
        select(d.Room, func.count(d.Room.players))
        .join(d.Player, d.Room.players)
        .where(d.Room.status != d.RoomStatusEnum.EXPIRED)
        .group_by(d.Room.id_)
    )
    result_tuples = result.fetchall()

    rooms_map = {}
    for room, player_count in result_tuples:
        room_out = s.RoomOut(players_no=player_count, **room.to_dict())
        rooms_map[room.id_] = room_out

    lobby_state = s.LobbyState(rooms=rooms_map)
    await conn_manager.send_lobby_state(player.id_, lobby_state)


async def handle_player_disconnect(
    player: d.Player, db: AsyncSession, conn_manager: ConnectionManager
) -> None:
    is_player_in_lobby = player.room_id == d.LOBBY.id_
    if not is_player_in_lobby:
        active_game_with_player = await db.scalar(
            select(d.Game).where(
                func.and_(
                    d.Game.status == d.GameStatusEnum.IN_PROGRESS,
                    d.Game.players.contains(player),
                )
            )
        )

        if not active_game_with_player:
            # If disconnected while in a game room, throw the player into the lobby
            player.room_id = d.LOBBY.id_
            db.add(player)
            await db.flush([player])

            message = d.Message(
                content=f'{player.name} disconnected...',
                room_id=player.room_id,
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
        content=f'{player.name} left the room',
        room_id=player.room_id,
        player_id=d.ROOT.id_,
    )
    await save_and_broadcast_message(message, db, conn_manager)


async def listen_for_messages(
    player: d.Player,
    websocket: WebSocket,
    db: AsyncSession,
    conn_manager: ConnectionManager,
):
    while True:
        # TODO: Make a wrapper which deserializes the websocket message when it arrives
        websocket_message_dict = await websocket.receive_json()
        websocket_message = s.WebSocketMessage(**websocket_message_dict)

        await db.refresh(player)
        match websocket_message.type:
            # TODO: Make a wrapper which handles CHAT type websocket messages
            case s.WebSocketMessageTypeEnum.CHAT:
                message = d.Message(
                    content=websocket_message.payload.content,
                    room_id=websocket_message.payload.room_id,
                    player=player,
                )
                await save_and_broadcast_message(message, db, conn_manager)
            case s.WebSocketMessageTypeEnum.GAME_STATE:
                pass

        # Commit all flushed resources to DB every time a message is received
        await db.commit()


async def send_lobby_state(
    player: d.Player, db: AsyncSession, conn_manager: ConnectionManager
):
    """
    Alternative way of refreshing the lobby state through a coroutine which would be
    polled inside the websocket endpoint. This simplifies code by avoiding event-based
    refreshing, for the price of not longer live updates. Currently NOT used.
    """
    room_count_tuple = await db.scalars(
        select(d.Room, func.count(d.Room.players)).where(
            d.Room.status != d.RoomStatusEnum.EXPIRED
        )
    )
    rooms_map = {}
    for room, player_count in room_count_tuple:
        room_out = s.RoomOut(players_no=player_count, **room.to_dict())
        rooms_map[room.id_] = room_out

    lobby_state = s.LobbyState(rooms=rooms_map)
    await conn_manager.broadcast_lobby_state(lobby_state)
