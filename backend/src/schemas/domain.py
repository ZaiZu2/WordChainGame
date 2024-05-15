from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass, field, fields, is_dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Literal, Protocol
from uuid import UUID

from fastapi import WebSocket

from config import get_config

# FILE STORING ONLY DOMAIN SCHEMAS USED AS INTERNAL DATA STRUCTURES


@dataclass
class DataclassMixin:
    def update(self, **kwargs):
        field_names = {f.name for f in fields(self)}
        for key, value in kwargs.items():
            if key in field_names:
                prev_dataclass = getattr(self, key)
                # If the field is a dataclass, create a new instance of it
                if is_dataclass(prev_dataclass):
                    setattr(self, key, prev_dataclass.__class__(**value))
                else:
                    setattr(self, key, value)

    def to_dict(self) -> dict:
        return asdict(self)


##### PLAYER #####


@dataclass(kw_only=True)
class Player(DataclassMixin):
    """Class storing transient connection (player) state."""

    id_: UUID
    name: str
    created_on: datetime
    room: Room

    # Here is also stored transient room data e.g. ready state, mute state, etc.
    ready: bool = False  # Flag necessary to start a game
    in_game: bool = False  # Flag denoting if the player is still in the game view (e.g. post-game statistics)

    websocket: WebSocket

    def __hash__(self) -> int:
        return self.id_.int

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Player):
            return self.id_ == other.id_
        return False

    def to_dict(self, depth: int = 1) -> dict:
        """
        Cast to a dict, serializing recursive fields to the given depth.

        Convenience method for passing domain models as dicts into Validation models,
        without the necessity to manually write fields as keyword arguments. `asdict`
        method is not used to avoid infinite recursion (e.g. `Player` and `Room` are
        referencing each other, leading to `asdict` recursion error.)
        """
        result = {
            'id_': self.id_,
            'name': self.name,
            'created_on': self.created_on,
            'ready': self.ready,
            'in_game': self.in_game,
        }
        if depth > 0:
            result['room'] = self.room.to_dict(depth=depth - 1)

        return result


@dataclass(kw_only=True)
class GamePlayer(DataclassMixin):
    id_: UUID
    name: str
    in_game: bool = True
    place: int | None = None
    score: int
    mistakes: int = 0


##### ROOM #####


class WordInputBuffer:
    """Buffer for propagating WordInput from the message listening coroutine to `run_game` coroutine."""

    def __init__(self):
        self._lock = asyncio.Lock()
        self._new_input_event = asyncio.Event()
        self._input = None

    async def put(self, input_) -> None:  #: s.WordInput
        async with self._lock:
            self._input = input_
            self._new_input_event.set()

    async def get(self) -> Any:  # s.WordInput
        await self._new_input_event.wait()
        async with self._lock:
            input_ = self._input
            self._input = None
            self._new_input_event.clear()
        return input_


class RoomStatusEnum(str, Enum):
    OPEN = 'Open'
    CLOSED = 'Closed'
    IN_PROGRESS = 'In progress'
    EXPIRED = 'Expired'


@dataclass(kw_only=True)
class Room(DataclassMixin):
    """Class storing transient room state."""

    id_: int
    name: str
    status: RoomStatusEnum = RoomStatusEnum.OPEN
    capacity: int
    created_on: datetime
    ended_on: datetime | None = None  # Unecessary, this info is persisted in ORM model
    owner: Player
    rules: DeathmatchRules
    players: dict[UUID, Player] = field(default_factory=dict)

    word_input_buffer: WordInputBuffer = WordInputBuffer()

    def __hash__(self) -> int:
        return hash(self.id_)

    def to_dict(self, depth: int = 1) -> dict:
        """
        Cast to a dict, optionally skipping serialization of recursive fields in child
        dataclasses.

        Convenience method for passing domain models as dicts into Validation models,
        without the necessity to manually write fields as keyword arguments. `asdict`
        method is not used to avoid infinite recursion (e.g. `Player` and `Room` are
        referencing each other, leading to `asdict` recursion error.)
        """
        result = {
            'id_': self.id_,
            'name': self.name,
            'status': self.status,
            'capacity': self.capacity,
            'created_on': self.created_on,
            'ended_on': self.ended_on,
            'rules': self.rules,
        }
        if depth > 0:
            result['owner'] = self.owner.to_dict(depth=depth - 1)
        return result


##### GAME #####


class GameStatusEnum(str, Enum):
    STARTED = 'STARTED'
    IN_PROGRESS = 'IN PROGRESS'
    FINISHED = 'FINISHED'


class GameTypeEnum(str, Enum):
    DEATHMATCH = 'deathmatch'


class GameStateEnum(str, Enum):
    CREATING = 'CREATING'
    STARTED = 'STARTED'
    ENDED = 'ENDED'
    WAITING = 'WAITING'
    STARTED_TURN = 'STARTED_TURN'
    ENDED_TURN = 'ENDED_TURN'


@dataclass(kw_only=True)
class Word:
    content: str | None = None
    description: list[tuple[str, str]] | None = None
    is_correct: bool | None = None

    def __hash__(self) -> int:
        return hash(self.content)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Word):
            return self.content == other.content
        return False


@dataclass(kw_only=True)
class Turn:
    word: Word | None = None
    started_on: datetime
    ended_on: datetime | None = None
    info: str | None = None
    player_id: UUID


@dataclass(kw_only=True)
class DeathmatchRules(DataclassMixin):
    type_: Literal[GameTypeEnum.DEATHMATCH] = GameTypeEnum.DEATHMATCH
    round_time: int
    start_score: int
    penalty: int
    reward: int


##### MESSAGE #####


@dataclass(kw_only=True)
class GameEvent(Protocol):
    type_: Literal['GameFinished', 'PlayerLost', 'IncorrectWord', 'CorrectWord']


@dataclass(kw_only=True)
class PlayerLostEvent(GameEvent):
    type_: Literal['PlayerLost'] = 'PlayerLost'
    player_name: str


@dataclass(kw_only=True)
class GameFinishedEvent(GameEvent):
    type_: Literal['GameFinished'] = 'GameFinished'


# Global root domain models representing server room & user, accessible to all components of the application
ROOT = Player(
    id_=get_config().ROOT_ID,
    name=get_config().ROOT_NAME,
    created_on=None,
    websocket=None,
    room=None,
)
LOBBY = Room(
    id_=get_config().LOBBY_ID,
    name=get_config().LOBBY_NAME,
    status=RoomStatusEnum.OPEN,
    capacity=None,
    created_on=None,
    owner=ROOT,
    rules=None,
)
ROOT.room = LOBBY
