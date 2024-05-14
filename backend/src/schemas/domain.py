from __future__ import annotations

import asyncio
from dataclasses import dataclass, field, fields, is_dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Annotated, Any, Literal, Protocol
from uuid import UUID

from fastapi import WebSocket
from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    PlainSerializer,
    validator,
)

from config import get_config

# FILE STORING ONLY DOMAIN SCHEMAS USED AS INTERNAL DATA STRUCTURES


class GeneralBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


def is_date_utc(date: datetime) -> datetime:
    if date.utcoffset() is not None and date.utcoffset() != timedelta(0):
        raise ValueError('Only datetimes in a UTC zone are allowed')
    date = date.replace(tzinfo=None)  # Cast to naive datetime after validation
    return date


# NOTE: Only UTC timestamps should be accepted by API server.
# NOTE: Currently used only for APITriggers, as zulu datetime formating can potentially break Desktop
UTCDatetime = Annotated[
    datetime,
    AfterValidator(is_date_utc),  # Validate if the date is in UTC zone (zulu format)
    PlainSerializer(
        lambda date: f'{date.isoformat()}Z', when_used='json'
    ),  # Serialize Timestamps to zulu format
]


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

                setattr(self, key, value)

    # def to_dict(self, skip_dataclasses: bool = False) -> dict:
    #     """
    #     Perform only a shallow serialization of the dataclass - only parent and it's
    #     children dataclasses will be serialized. Any child backreferencing the parent
    #     will be skipped. This avoids infinite recursion in the serialization process.

    #     Example:
    #     -------
    #     `Player` and `Room` are referencing each other, leading to `asdict` recursion error.
    #     """
    #     result = {}
    #     for f in fields(self):
    #         value = getattr(self, f.name)

    #         if is_dataclass(value) and f.metadata.get('backref') is True:
    #             if skip_dataclasses:
    #                 continue
    #             result[f.name] = value.to_dict(skip_dataclasses=True)
    #         else:
    #             result[f.name] = value
    #     return result


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


class GamePlayer(GeneralBaseModel):
    id_: UUID
    name: str
    in_game: bool = True
    place: int | None = None
    score: int
    mistakes: int = 0

    @validator('in_game')
    @classmethod
    def validate_in_game(cls, in_game, values):
        if not in_game and values.get('place') is None:
            raise ValueError('`place` must be set if `in_game` is changed to False')
        return in_game


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
            # result['players'] = {
            #     player_id: player.to_dict(depth=depth - 1)
            #     for player_id, player in self.players.items()
            # }
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
    started_on: UTCDatetime
    ended_on: UTCDatetime | None = None
    info: str | None = None
    player_id: UUID


@dataclass(kw_only=True)
class DeathmatchRules:
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
    # rules=DeathmatchRules(
    #     type_=GameTypeEnum.DEATHMATCH, round_time=60, start_score=0, penalty=0, reward=0
    # ),
)
ROOT.room = LOBBY
