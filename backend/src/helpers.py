from enum import Enum

from fastapi import WebSocket, WebSocketException
from sqlalchemy.ext.asyncio import AsyncSession

import src.models as d  # d - database
import src.schemas as s  # s - schema
from src.connection_manager import ConnectionManager
from src.models import get_root_player


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
    await conn_manager.broadcast_chat_message(message)


async def accept_websocket_connection(
    player: d.Player,
    websocket: WebSocket,
    db: AsyncSession,
    conn_manager: ConnectionManager,
) -> None:
    root_player = await get_root_player(db)

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
            player=root_player,
        )
        await save_and_send_message(message, db, conn_manager)

        db.commit()
        raise WebSocketException(
            s.CustomWebsocketCodeEnum.MULTIPLE_CLIENTS,
            'Player is already connected with another client',
        )

    message = d.Message(
        content=f'{player.name} joined the room',
        room_id=player.room_id,
        player=root_player,
    )
    await save_and_send_message(message, db, conn_manager)
    db.commit()
