from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.ext.asyncio import AsyncAttrs

import src.schemas.domain as d

# FILE STORING ONLY ORM SCHEMAS USED AS PERSISTANCE MODELS
# NOTE: CASCADE ON DELETE behavior not resolved as no resources are to be deleted in this project

metadata = sa.MetaData(
    naming_convention={
        'ix': 'ix_%(column_0_label)s',
        'uq': 'uq_%(table_name)s_%(column_0_name)s',
        'ck': 'ck_%(table_name)s_%(constraint_name)s',
        'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
        'pk': 'pk_%(table_name)s',
    }
)


class Base(AsyncAttrs, so.DeclarativeBase):
    metadata = metadata
    pass

    def to_dict(self) -> dict:
        return {
            col_name: getattr(self, col_name) for col_name in self.__mapper__.c.keys()
        }

    def update(self, data: dict) -> None:
        for column, value in data.items():
            setattr(self, column, value)


players_games_table = sa.Table(
    'players_games',
    Base.metadata,
    sa.Column('player_id', sa.ForeignKey('players.id'), primary_key=True),
    sa.Column('game_id', sa.ForeignKey('games.id'), primary_key=True),
)


class Player(Base):
    __tablename__ = 'players'

    id_: so.Mapped[UUID] = so.mapped_column('id', primary_key=True, default=uuid4)
    name: so.Mapped[str] = so.mapped_column(sa.String(10), unique=True)
    created_on: so.Mapped[datetime] = so.mapped_column(default=sa.func.now())
    # last_active_on: so.Mapped[datetime] = so.mapped_column(default=sa.func.now())

    messages: so.Mapped[list[Message]] = so.relationship(back_populates='player')
    turns: so.Mapped[list[Turn]] = so.relationship(back_populates='player')
    games: so.Mapped[list[Game]] = so.relationship(
        secondary=players_games_table, back_populates='players'
    )


class Room(Base):
    __tablename__ = 'rooms'

    id_: so.Mapped[int] = so.mapped_column('id', primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(10), unique=True)
    created_on: so.Mapped[datetime] = so.mapped_column(default=sa.func.now())
    last_active_on: so.Mapped[datetime] = so.mapped_column(default=sa.func.now())
    ended_on: so.Mapped[datetime | None] = so.mapped_column()

    games: so.Mapped[list[Game]] = so.relationship(back_populates='room')
    messages: so.Mapped[list[Message]] = so.relationship(back_populates='room')


class GameStatusEnum(str, Enum):
    """DB-specific enum, subsetting the domain enum."""

    STARTED = d.GameStateEnum.STARTED
    ENDED = d.GameStateEnum.ENDED


class Game(Base):
    __tablename__ = 'games'

    id_: so.Mapped[int] = so.mapped_column('id', primary_key=True)
    status: so.Mapped[GameStatusEnum] = so.mapped_column(nullable=False)
    created_on: so.Mapped[datetime] = so.mapped_column(default=sa.func.now())
    ended_on: so.Mapped[datetime | None] = so.mapped_column()
    rules: so.Mapped[dict] = so.mapped_column(sa.JSON)  # TODO: Add TypedDict for rules

    room_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('rooms.id'))
    room: so.Mapped[Room] = so.relationship(back_populates='games')

    turns: so.Mapped[list[Turn]] = so.relationship(back_populates='game')
    players: so.Mapped[list[Player]] = so.relationship(
        secondary=players_games_table, back_populates='games'
    )


# Acts as a Domain model as well as internal schema does not differ from the database schema
class Message(Base):
    __tablename__ = 'messages'

    id_: so.Mapped[int] = so.mapped_column('id', primary_key=True)
    content: so.Mapped[str] = so.mapped_column(sa.String(255))
    created_on: so.Mapped[datetime] = so.mapped_column(default=sa.func.now())

    room_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('rooms.id'))
    room: so.Mapped[Room] = so.relationship(back_populates='messages')
    player_id: so.Mapped[UUID] = so.mapped_column(sa.ForeignKey('players.id'))
    player: so.Mapped[Player] = so.relationship(back_populates='messages')


# TODO: Add composite unique constraint on `word` and `game_id`?
class Turn(Base):
    __tablename__ = 'turns'
    __table_args__ = (
        CheckConstraint(
            '(word IS NULL AND is_correct IS NULL) OR (word IS NOT NULL AND is_correct IS NOT NULL)',
            name='word_is_correct_co_nullable',
        ),
        UniqueConstraint('word', 'game_id', name='word_game_id_unique'),
    )

    id_: so.Mapped[int] = so.mapped_column('id', primary_key=True)
    word: so.Mapped[str | None] = so.mapped_column(sa.String(255))
    is_correct: so.Mapped[bool | None] = so.mapped_column()
    started_on: so.Mapped[datetime] = so.mapped_column(default=sa.func.now())
    ended_on: so.Mapped[datetime | None] = so.mapped_column(nullable=True)

    game_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('games.id'))
    game: so.Mapped[Game] = so.relationship(back_populates='turns')
    player_id: so.Mapped[UUID] = so.mapped_column(sa.ForeignKey('players.id'))
    player: so.Mapped[Player] = so.relationship(back_populates='turns')
