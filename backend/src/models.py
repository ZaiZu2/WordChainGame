from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

import sqlalchemy as sa
import sqlalchemy.orm as so
from async_lru import alru_cache
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

import src.models as d
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


class Base(AsyncAttrs, so.DeclarativeBase):
    metadata = metadata
    pass


# NOTE: CASCADE ON DELETE behavior not resolved as no resources are to be deleted in this project

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
    last_active_on: so.Mapped[datetime] = so.mapped_column(default=sa.func.now())

    room_id: so.Mapped[int] = so.mapped_column(
        # FK check must be deferred when creating 'root' and 'lobby' on server startup
        # due to circular dependency
        sa.ForeignKey('rooms.id', deferrable=True),
        default=1,
    )
    room: so.Mapped[Room] = so.relationship(
        back_populates='players', foreign_keys=[room_id]
    )

    messages: so.Mapped[list[Message]] = so.relationship(back_populates='player')
    words: so.Mapped[list[Word]] = so.relationship(back_populates='player')
    games: so.Mapped[list[Game]] = so.relationship(
        secondary=players_games_table, back_populates='players'
    )


class Room(Base):
    __tablename__ = 'rooms'

    id_: so.Mapped[int] = so.mapped_column('id', primary_key=True)
    name: so.Mapped[str] = so.mapped_column(
        sa.String(10), unique=True
    )  # NOTE: Should this be unique?
    created_on: so.Mapped[datetime] = so.mapped_column(default=sa.func.now())
    ended_on: so.Mapped[datetime | None] = so.mapped_column()
    rules: so.Mapped[dict] = so.mapped_column(sa.JSON)  # TODO: Add TypedDict for rules

    owner_id: so.Mapped[UUID] = so.mapped_column(sa.ForeignKey('players.id'))
    owner: so.Mapped[Player] = so.relationship(foreign_keys=[owner_id])

    players: so.Mapped[list[Player]] = so.relationship(
        back_populates='room', foreign_keys=[Player.room_id]
    )
    games: so.Mapped[list[Game]] = so.relationship(back_populates='room')
    messages: so.Mapped[list[Message]] = so.relationship(back_populates='room')


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

    room_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('rooms.id'))
    room: so.Mapped[Room] = so.relationship(back_populates='games')

    words: so.Mapped[list[Word]] = so.relationship(back_populates='game')
    players: so.Mapped[list[Player]] = so.relationship(
        secondary=players_games_table, back_populates='games'
    )


class Message(Base):
    __tablename__ = 'messages'

    id_: so.Mapped[int] = so.mapped_column('id', primary_key=True)
    content: so.Mapped[str] = so.mapped_column(sa.String(255))
    created_on: so.Mapped[datetime] = so.mapped_column(default=sa.func.now())

    room_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('rooms.id'))
    room: so.Mapped[Room] = so.relationship(back_populates='messages')
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


async def recreate_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def create_root_objects():
    """Create a db representations of a lobby chat and the it's necessary owner on server startup."""
    async with async_session() as db:
        try:
            await db.begin()
            # Root objects have circular FK constraints - this can happen only here
            await db.execute(
                sa.text('SET CONSTRAINTS fk_players_room_id_rooms DEFERRED')
            )

            if await db.scalar(select(d.Room).where(d.Room.id_ == 1)):
                raise ValueError(
                    f'Table "{d.Room.__tablename__}" is not empty - "lobby" room must be created with id=1'
                )
            if await db.scalar(select(d.Player).where(d.Player.name == 'root')):
                raise ValueError(
                    f'Table "{d.Room.__tablename__}" is not empty - Root player must be created with the name "root"'
                )

            global ROOT, LOBBY
            ROOT.room_id = LOBBY.id_
            db.add_all([LOBBY, ROOT])
            await db.commit()
            await db.refresh(LOBBY)
            so.make_transient(LOBBY)
            await db.refresh(ROOT)
            so.make_transient(ROOT)
        except Exception:
            await db.rollback()
            raise


# Global root db objects, accessible to all components of the application
# Their dynamic attrs (id, ...) are set in `create_root_objects()` on webserver startup
ROOT = Player(name='root')
LOBBY = Room(name='lobby', status=RoomStatusEnum.OPEN, owner=ROOT, rules={})
