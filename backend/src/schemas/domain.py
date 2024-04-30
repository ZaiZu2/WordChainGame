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
    validator,
)

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


class Player(GeneralBaseModel):
    id_: UUID = Field(serialization_alias='id')
    name: str
    created_on: UTCDatetime


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


class GameTypeEnum(str, Enum):
    DEATHMATCH = 'deathmatch'


class GameStateEnum(str, Enum):
    CREATING = 'CREATING'
    STARTING = 'STARTING'
    ENDING = 'ENDING'
    WAITING = 'WAITING'
    START_TURN = 'START_TURN'
    END_TURN = 'END_TURN'


class Word(GeneralBaseModel):
    content: str | None = None
    description: list[tuple[str, str]] | None = None
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


class GameEvent(Protocol):
    type_: Literal['GameFinished', 'PlayerLost', 'IncorrectWord', 'CorrectWord']


class PlayerLostEvent(GeneralBaseModel):
    type_: Literal['PlayerLost'] = 'PlayerLost'
    player_name: str


class GameFinishedEvent(GeneralBaseModel):
    type_: Literal['GameFinished'] = 'GameFinished'
