from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Annotated, AsyncGenerator, Literal
from uuid import UUID

from fastapi import (
    Cookie,
    Depends,
    HTTPException,
    Response,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

import src.database as d  # d - database
from config import Config, get_config
from src.connection_manager import ConnectionManager
from src.database import async_session
from src.game.game import GameManager


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency injection function to pass a db session into endpoints.

    FastAPI internally wraps this function into an async context manager, so it cannot
    be used as a context manager itself.
    """
    async with async_session() as session:
        try:
            await session.begin()
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def init_db_session() -> AsyncGenerator[AsyncSession, None]:
    """A `get_db` clone, but can be used as a stand-alone async context manager."""  # noqa: D401
    async with async_session() as session:
        try:
            await session.begin()
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@lru_cache
def get_connection_manager() -> ConnectionManager:
    """FastAPI dependency injection function to pass a ConnectionManager instance into endpoints."""
    return ConnectionManager()


@lru_cache
def get_game_manager() -> GameManager:
    """FastAPI dependency injection function to pass a GameManager instance into endpoints."""
    return GameManager()


async def get_player(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    player_id: Annotated[UUID | Literal[''] | None, Cookie()] = None,
) -> d.Player:
    if player_id is None or player_id == '':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Player is not authenticated',
        )

    player = await db.scalar(select(d.Player).where(d.Player.id_ == player_id))
    if not player:
        await set_auth_cookie('', response)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Player is not authenticated',
        )

    await set_auth_cookie(player_id, response)
    return player


async def get_room(
    room_id: int,
    player: Annotated[d.Player, Depends(get_player)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> d.Room:
    room = await db.scalar(
        select(d.Room).where(d.Room.id_ == room_id).options(joinedload(d.Room.owner))
    )
    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Room not found'
        )
    return room


async def set_auth_cookie(
    value: UUID | Literal[''],
    response: Response,
    config: Config = get_config(),  # noqa
) -> None:
    response.set_cookie(
        key=config.AUTH_COOKIE_NAME,
        value=str(value),
        max_age=config.AUTH_COOKIE_EXPIRATION,
        httponly=True,
        samesite='none',
        secure=True,
    )
