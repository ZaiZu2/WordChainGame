from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

import src.schemas.database as db
from config import get_config

engine = create_async_engine(get_config().DATABASE_URI)
async_session = async_sessionmaker(bind=engine, autocommit=False, autoflush=True)


@asynccontextmanager
async def init_db_session() -> AsyncGenerator[AsyncSession, None]:
    """A `get_db` dependency clone, but can be used as a stand-alone async context manager."""  # noqa: D401
    async with async_session() as session:
        try:
            await session.begin()
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def recreate_database():
    async with engine.begin() as conn:  # `engine.begin()` due to a synchronous DB commands
        await conn.run_sync(db.Base.metadata.drop_all)
        await conn.run_sync(db.Base.metadata.create_all)


async def create_root_objects():
    """Create a db representations of a lobby chat and the it's necessary owner on server startup."""
    async with init_db_session() as db_session:
        if await db_session.scalar(select(db.Room).where(db.Room.id_ == 1)):
            raise ValueError(
                f'Table "{db.Room.__tablename__}" is not empty - "lobby" db.room must be created with id=1'
            )
        if await db_session.scalar(select(db.Player).where(db.Player.name == 'root')):
            raise ValueError(
                f'Table "{db.Room.__tablename__}" is not empty - Root player must be created with the name "root"'
            )

        root = db.Player(id_=get_config().ROOT_ID, name=get_config().ROOT_NAME)
        assert get_config().LOBBY_ID == 1  # Ensure that the lobby ID is 1
        lobby = db.Room(
            name=get_config().LOBBY_NAME
        )  # Do not pass ID as it is autoincremented
        db_session.add_all([lobby, root])
