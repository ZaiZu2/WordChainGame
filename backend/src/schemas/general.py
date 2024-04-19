from datetime import datetime, timedelta
from enum import Enum
from typing import Annotated, Any, Literal, Protocol
from uuid import UUID

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    PlainSerializer,
)

import src.models as d


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

#################################### DOMAIN SCHEMAS ####################################


class Player(GeneralBaseModel):
    id_: UUID = Field(serialization_alias='id')
    name: str
    created_on: UTCDatetime


class GameTypeEnum(str, Enum):
    DEATHMATCH = 'deathmatch'


class Rules(GeneralBaseModel):
    type_: GameTypeEnum = Field(serialization_alias='type')


class DeathmatchRules(Rules):
    type_: Literal[GameTypeEnum.DEATHMATCH] = Field(
        GameTypeEnum.DEATHMATCH, serialization_alias='type'
    )
    round_time: int = Field(10, ge=3, le=30)
    start_score: int = Field(0, ge=0, le=10)
    penalty: int = Field(-5, ge=-10, le=0)  # If 0, player loses after a single mistake
    reward: int = Field(2, ge=0, le=10)


class ChatMessage(GeneralBaseModel):
    id_: int | None = Field(None, serialization_alias='id')
    created_on: UTCDatetime | None = None
    content: str
    player_name: str
    room_id: int


class CurrentStatistics(GeneralBaseModel):
    active_players: int
    active_rooms: int


class AllTimeStatistics(GeneralBaseModel):
    longest_chain: int
    longest_game_time: int
    total_games: int


class Word(GeneralBaseModel):
    content: str | None = None
    description: dict[str, str] | None = None
    is_correct: bool | None = None

    def __hash__(self) -> int:
        return hash(self.content)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Word):
            return self.content == other.content
        return False


class Turn(GeneralBaseModel):
    word: Word | None = None
    started_on: UTCDatetime
    ended_on: UTCDatetime | None = None
    info: str | None = None
    player_id: UUID


class TurnOut(GeneralBaseModel):
    word: Word | None = None
    started_on: UTCDatetime
    ended_on: UTCDatetime | None = None
    info: str | None = None
    player_idx: int


class GameEvent(Protocol):
    type_: Literal['GameFinished', 'PlayerLost', 'IncorrectWord', 'CorrectWord']


class PlayerLostEvent(GeneralBaseModel):
    type_: Literal['PlayerLost'] = 'PlayerLost'
    player_name: str


class GameFinishedEvent(GeneralBaseModel):
    type_: Literal['GameFinished'] = 'GameFinished'


################################## VALIDATION SCHEMAS ##################################


class LobbyPlayerOut(GeneralBaseModel):
    """Player data sent as a part of LobbyState."""

    name: str
    created_on: UTCDatetime


class RoomPlayerOut(LobbyPlayerOut):
    """Player data sent as a part of RoomState."""

    ready: bool


class GamePlayer(GeneralBaseModel):
    id_: UUID
    name: str
    score: int
    mistakes: int


class RoomOut(GeneralBaseModel):
    id_: int = Field(serialization_alias='id')
    name: str
    players_no: int
    capacity: int
    status: d.RoomStatusEnum
    rules: DeathmatchRules
    owner_name: str


class RoomIn(GeneralBaseModel):
    name: str = Field(..., max_length=10)
    capacity: int = Field(5, ge=1, le=10)
    rules: DeathmatchRules


class RoomInModify(GeneralBaseModel):
    capacity: int = Field(5, ge=1, le=10)
    rules: DeathmatchRules
