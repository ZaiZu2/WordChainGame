from datetime import datetime
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
from sqlalchemy.ext.asyncio import AsyncSession

import src.schemas.domain as d
from config import Config, get_config
from src.connection_manager import ConnectionManager
from src.database import async_session
from src.game.game import GameManager
from src.player_room_manager import player_room_pool


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
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


@lru_cache
def get_connection_manager() -> ConnectionManager:
    """FastAPI dependency injection function to pass a ConnectionManager instance into endpoints."""
    return ConnectionManager(pool=player_room_pool)


@lru_cache
def get_game_manager() -> GameManager:
    """FastAPI dependency injection function to pass a GameManager instance into endpoints."""
    return GameManager()


async def get_player(
    response: Response,
    conn_manager: Annotated[ConnectionManager, Depends(get_connection_manager)],
    player_id: Annotated[UUID | Literal[''] | None, Cookie()] = None,
) -> d.Player:
    if player_id is None or player_id == '':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Player is not authenticated',
        )

    try:
        player = conn_manager.pool.get_player(player_id)  # type: ignore
    except KeyError:
        await set_auth_cookie('', response)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Player is not authenticated',
        ) from None

    # Extend cookie's expiration time, after each new, successful request
    await set_auth_cookie(player_id, response)
    return player


async def get_room(
    room_id: int,
    player: Annotated[d.Player, Depends(get_player)],
    conn_manager: Annotated[ConnectionManager, Depends(get_connection_manager)],
) -> d.Room:
    room = conn_manager.pool.get_room(room_id=room_id)

    # Any room endpoint accessed by the owner should refresh room's `last_active_on`
    if room.owner.id_ == player.id_:
        room.last_active_on = datetime.utcnow()

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
