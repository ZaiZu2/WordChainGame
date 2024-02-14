from enum import Enum

from fastapi import WebSocket, WebSocketException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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


async def save_and_send_message(
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
        # Send a message to the duplicate client, then terminate the connection
        await conn_manager.send_connection_state(
            s.CustomWebsocketCodeEnum.MULTIPLE_CLIENTS,
            'Player is already connected with another client.',
            websocket,
        )

        # Inform the original client about the connection attempt
        message = d.Message(
            content='Someone tried to log into your account from another device. If it was not you, please regenerate your account code.',
            room_id=player.room_id,
            player=d.ROOT,
        )
        await save_and_send_message(message, db, conn_manager)
        raise WebSocketException(
            s.CustomWebsocketCodeEnum.MULTIPLE_CLIENTS,
            'Player is already connected with another client',
        )

    message = d.Message(
        content=f'{player.name} joined the room',
        room_id=player.room_id,
        player_id=d.ROOT.id_,
    )
    await save_and_send_message(message, db, conn_manager)


async def send_initial_state(
    player: d.Player, db: AsyncSession, conn_manager: ConnectionManager
):
    """
    Send room specific state upon player's connection. If the player is in the lobby,
    send the lobby state. If a game in which player is participating is still on,
    reconnect him.
    """
    # 1.
    # TODO: Check and reconnect if the player was disconnected from any on-going game
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

    # 2. Switch to Lobby if player disconnected from a different room
    if player.room_id != d.LOBBY.id_:
        player.room_id = d.LOBBY.id_
        db.add(player)
        db.flush([player])

    rooms = await db.scalars(select(d.Room).options(selectinload(d.Room.players)))
    rooms_map = {}
    for room in rooms:
        room_out = s.RoomOut(players_no=len(room.players), **room.to_dict())
        rooms_map[room.id_] = room_out

    lobby_state = s.LobbyState(rooms=rooms_map)
    await conn_manager.send_lobby_state(player.id_, lobby_state)
