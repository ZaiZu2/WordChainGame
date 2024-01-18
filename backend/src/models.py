from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

import sqlalchemy as sa
import sqlalchemy.orm as so
from fastapi import Depends, HTTPException, status, Cookie
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from typing import Annotated

from config import get_config

metadata = sa.MetaData(
    naming_convention={
        'ix': 'ix_%(column_0_label)s',
        'uq': 'uq_%(table_name)s_%(column_0_name)s',
        'ck': 'ck_%(table_name)s_%(constraint_name)s',
        'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
        'pk': 'pk_%(table_name)s',
    }
)


engine = create_async_engine(get_config().DATABASE_URI)
async_session = async_sessionmaker(bind=engine, autocommit=False, autoflush=True)


async def get_db() -> AsyncSession:
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.drop_all)
    #     await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        try:
            await session.begin()
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_user(
    user_id: Annotated[UUID, Cookie()], db: AsyncSession = Depends(get_db)
) -> Player:
    player = await db.scalar(sa.select(Player).where(Player.id_ == user_id))
    if not player:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail='User not found'
        )
    return player


class Base(AsyncAttrs, so.DeclarativeBase):
    metadata = metadata
    pass


# NOTE: CASCADE ON DELETE behavior not resolved as no resources are to be deleted in this project


# Association table for many-to-many relationship between `players` and `games`
players_games_table = sa.Table(
    'players_games',
    Base.metadata,
    sa.Column('player_id', sa.ForeignKey('players.id'), primary_key=True),
    sa.Column('game_id', sa.ForeignKey('games.id'), primary_key=True),
)


class Player(Base):
    __tablename__ = 'players'

    id_: so.Mapped[UUID] = so.mapped_column('id', primary_key=True, default=uuid4)
    name: so.Mapped[str] = so.mapped_column(sa.String(15), unique=True)
    created_on: so.Mapped[datetime] = so.mapped_column(default=sa.func.now())
    last_active_on: so.Mapped[datetime] = so.mapped_column(default=sa.func.now())

    game_room_id: so.Mapped[int | None] = so.mapped_column(
        sa.ForeignKey('game_rooms.id')
    )
    game_room: so.Mapped[GameRoom | None] = so.relationship(
        back_populates='players', foreign_keys=[game_room_id]
    )

    messages: so.Mapped[list[Message]] = so.relationship(back_populates='player')
    words: so.Mapped[list[Word]] = so.relationship(back_populates='player')
    games: so.Mapped[list[Game]] = so.relationship(
        secondary=players_games_table, back_populates='players'
    )


class GameRoom(Base):
    __tablename__ = 'game_rooms'

    id_: so.Mapped[int] = so.mapped_column('id', primary_key=True)
    name: so.Mapped[str] = so.mapped_column(
        sa.String(15), unique=True
    )  # NOTE: Should this be unique?
    created_on: so.Mapped[datetime] = so.mapped_column(default=sa.func.now())
    ended_on: so.Mapped[datetime | None] = so.mapped_column()
    rules: so.Mapped[dict] = so.mapped_column(sa.JSON)  # TODO: Add TypedDict for rules

    owner_id: so.Mapped[UUID] = so.mapped_column(sa.ForeignKey('players.id'))
    owner: so.Mapped[Player] = so.relationship(foreign_keys=[owner_id])

    players: so.Mapped[list[Player]] = so.relationship(
        back_populates='game_room', foreign_keys=[Player.game_room_id]
    )
    games: so.Mapped[list[Game]] = so.relationship(back_populates='game_room')
    messages: so.Mapped[list[Message]] = so.relationship(back_populates='game_room')


class GameStatusEnum(str, Enum):
    IN_PROGRESS = 'In progress'
    OPEN = 'Open'
    CLOSED = 'Closed'


class Game(Base):
    __tablename__ = 'games'

    id_: so.Mapped[int] = so.mapped_column('id', primary_key=True)
    status: so.Mapped[GameStatusEnum] = so.mapped_column(nullable=False)
    created_on: so.Mapped[datetime] = so.mapped_column(default=sa.func.now())
    ended_on: so.Mapped[datetime | None] = so.mapped_column()
    rules: so.Mapped[dict] = so.mapped_column(sa.JSON)  # TODO: Add TypedDict for rules

    game_room_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('game_rooms.id'))
    game_room: so.Mapped[GameRoom] = so.relationship(back_populates='games')

    words: so.Mapped[list[Word]] = so.relationship(back_populates='game')
    players: so.Mapped[list[Player]] = so.relationship(
        secondary=players_games_table, back_populates='games'
    )


class Message(Base):
    __tablename__ = 'messages'

    id_: so.Mapped[int] = so.mapped_column('id', primary_key=True)
    content: so.Mapped[str] = so.mapped_column(sa.String(255))
    created_on: so.Mapped[datetime] = so.mapped_column(default=sa.func.now())

    # NOTE: If `game_room==None`, the message is sent in the global chat
    game_room_id: so.Mapped[int | None] = so.mapped_column(
        sa.ForeignKey('game_rooms.id')
    )
    game_room: so.Mapped[GameRoom | None] = so.relationship(back_populates='messages')
    player_id: so.Mapped[UUID] = so.mapped_column(sa.ForeignKey('players.id'))
    player: so.Mapped[Player] = so.relationship(back_populates='messages')


# TODO: Add composite unique constraint on `content` and `game_id`?
class Word(Base):
    __tablename__ = 'words'

    id_: so.Mapped[int] = so.mapped_column('id', primary_key=True)
    content: so.Mapped[str] = so.mapped_column(sa.String(255))
    is_correct: so.Mapped[bool] = so.mapped_column()
    created_on: so.Mapped[datetime] = so.mapped_column(default=sa.func.now())

    game_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('games.id'))
    game: so.Mapped[Game] = so.relationship(back_populates='words')

    player_id: so.Mapped[UUID] = so.mapped_column(sa.ForeignKey('players.id'))
    player: so.Mapped[Player] = so.relationship(back_populates='words')
