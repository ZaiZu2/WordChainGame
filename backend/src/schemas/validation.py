from __future__ import annotations

from datetime import datetime, timedelta
from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    PlainSerializer,
)

import src.schemas.domain as m

# FILE STORING ONLY VALIDATION SCHEMAS USED AS RESTAPI INPUTS/OUTPUTS


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


class CurrentStatistics(GeneralBaseModel):
    active_players: int
    active_rooms: int


class AllTimeStatistics(GeneralBaseModel):
    longest_chain: int
    longest_game_time: int
    total_games: int


class TurnOut(GeneralBaseModel):
    word: m.Word | None = None
    started_on: UTCDatetime
    ended_on: UTCDatetime | None = None
    info: str | None = None
    player_idx: int


class Player(GeneralBaseModel):
    id_: UUID = Field(serialization_alias='id')
    name: str
    created_on: UTCDatetime


class LobbyPlayerOut(GeneralBaseModel):
    """Player data sent as a part of LobbyState."""

    name: str


class RoomPlayerOut(LobbyPlayerOut):
    """Player data sent as a part of RoomState."""

    ready: bool
    in_game: bool


class GamePlayer(GeneralBaseModel):
    name: str
    in_game: bool = True
    place: int | None = None
    score: int
    mistakes: int


class Rules(GeneralBaseModel):
    type_: m.GameTypeEnum = Field(serialization_alias='type')


class DeathmatchRules(Rules):
    type_: Literal[m.GameTypeEnum.DEATHMATCH] = Field(
        m.GameTypeEnum.DEATHMATCH, serialization_alias='type'
    )
    round_time: int = Field(10, ge=3, le=30)
    start_score: int = Field(0, ge=0, le=10)
    penalty: int = Field(-5, ge=-10, le=0)  # If 0, player loses after a single mistake
    reward: int = Field(2, ge=0, le=10)


class RoomOut(GeneralBaseModel):
    id_: int = Field(serialization_alias='id')
    name: str
    players_no: int
    capacity: int
    status: m.RoomStatusEnum
    rules: DeathmatchRules
    owner_name: str


class RoomIn(GeneralBaseModel):
    name: str = Field(..., max_length=10)
    capacity: int = Field(5, ge=1, le=10)
    rules: DeathmatchRules


class RoomInModify(GeneralBaseModel):
    capacity: int = Field(5, ge=1, le=10)
    rules: DeathmatchRules


# HACK: Avoid circular import issue between `validation.py` and `websockets.py` while
# exposing websocket schemas under `validation.*` namespace
from src.schemas.websockets import *  # noqa: E402, F403
