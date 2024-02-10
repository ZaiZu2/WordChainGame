from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession

import src.models as d  # d - database
from src.connection_manager import ConnectionManager


class TagsEnum(str, Enum):
    ALL = 'all'


tags_metadata = [
    {
        'name': TagsEnum.ALL,
        'description': 'All routes',
    },
]


async def persist_and_save_message(
    message: d.Message, db: AsyncSession, conn_manager: ConnectionManager
) -> None:
    db.add(message)
    await db.commit()
    await db.refresh(message, attribute_names=['player'])
    await conn_manager.broadcast_chat_message(message)
