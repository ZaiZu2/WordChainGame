from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
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

    def to_dict(self) -> dict:
        return {
            col_name: getattr(self, col_name) for col_name in self.__mapper__.c.keys()
        }


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

    messages: so.Mapped[list[Message]] = so.relationship(back_populates='player')
    words: so.Mapped[list[Word]] = so.relationship(back_populates='player')
    games: so.Mapped[list[Game]] = so.relationship(
        secondary=players_games_table, back_populates='players'
    )


class RoomStatusEnum(str, Enum):
    OPEN = 'Open'
    CLOSED = 'Closed'
    PRIVATE = 'Private'
    EXPIRED = 'Expired'


class Room(Base):
    __tablename__ = 'rooms'

    id_: so.Mapped[int] = so.mapped_column('id', primary_key=True)
    name: so.Mapped[str] = so.mapped_column(
        sa.String(10), unique=True
    )  # NOTE: Should this be unique?
    status: so.Mapped[RoomStatusEnum] = so.mapped_column(
        default=RoomStatusEnum.OPEN, nullable=False
    )
    capacity: so.Mapped[int] = so.mapped_column(nullable=False)
    created_on: so.Mapped[datetime] = so.mapped_column(default=sa.func.now())
    ended_on: so.Mapped[datetime | None] = so.mapped_column()
    rules: so.Mapped[dict] = so.mapped_column(sa.JSON)  # TODO: Add TypedDict for rules

    owner_id: so.Mapped[UUID] = so.mapped_column(sa.ForeignKey('players.id'))
    owner: so.Mapped[Player] = so.relationship(foreign_keys=[owner_id])

    games: so.Mapped[list[Game]] = so.relationship(back_populates='room')
    messages: so.Mapped[list[Message]] = so.relationship(back_populates='room')


class GameStatusEnum(str, Enum):
    IN_PROGRESS = 'In progress'
    FINISHED = 'Finished'


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

            if await db.scalar(select(d.Room).where(d.Room.id_ == 1)):
                raise ValueError(
                    f'Table "{d.Room.__tablename__}" is not empty - "lobby" room must be created with id=1'
                )
            if await db.scalar(select(d.Player).where(d.Player.name == 'root')):
                raise ValueError(
                    f'Table "{d.Room.__tablename__}" is not empty - Root player must be created with the name "root"'
                )

            global ROOT, LOBBY
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
LOBBY = Room(name='lobby', status=RoomStatusEnum.OPEN, capacity=0, owner=ROOT, rules={})
