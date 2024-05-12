from typing import Literal
from uuid import UUID

from pydantic import Field

import src.schemas.domain as m

# FILE STORING ONLY VALIDATION SCHEMAS USED AS RESTAPI INPUTS/OUTPUTS


class CurrentStatistics(m.GeneralBaseModel):
    active_players: int
    active_rooms: int


class AllTimeStatistics(m.GeneralBaseModel):
    longest_chain: int
    longest_game_time: int
    total_games: int


class TurnOut(m.GeneralBaseModel):
    word: m.Word | None = None
    started_on: m.UTCDatetime
    ended_on: m.UTCDatetime | None = None
    info: str | None = None
    player_idx: int


class Player(m.GeneralBaseModel):
    id_: UUID = Field(serialization_alias='id')
    name: str
    created_on: m.UTCDatetime


class LobbyPlayerOut(m.GeneralBaseModel):
    """Player data sent as a part of LobbyState."""

    name: str


class RoomPlayerOut(LobbyPlayerOut):
    """Player data sent as a part of RoomState."""

    ready: bool
    in_game: bool


class Rules(m.GeneralBaseModel):
    type_: m.GameTypeEnum = Field(serialization_alias='type')


class DeathmatchRulesIn(Rules):
    type_: Literal[m.GameTypeEnum.DEATHMATCH] = Field(
        m.GameTypeEnum.DEATHMATCH, serialization_alias='type'
    )
    round_time: int = Field(10, ge=3, le=30)
    start_score: int = Field(0, ge=0, le=10)
    penalty: int = Field(-5, ge=-10, le=0)  # If 0, player loses after a single mistake
    reward: int = Field(2, ge=0, le=10)


class RoomOut(m.GeneralBaseModel):
    id_: int = Field(serialization_alias='id')
    name: str
    players_no: int
    capacity: int
    status: m.RoomStatusEnum
    rules: DeathmatchRulesIn
    owner_name: str


class RoomIn(m.GeneralBaseModel):
    name: str = Field(..., max_length=10)
    capacity: int = Field(5, ge=1, le=10)
    rules: DeathmatchRulesIn


class RoomInModify(m.GeneralBaseModel):
    capacity: int = Field(5, ge=1, le=10)
    rules: DeathmatchRulesIn


# HACK: Avoid circular import issue between `validation.py` and `websockets.py` while
# exposing websocket schemas under `validation.*` namespace
from src.schemas.websockets import *  # noqa: E402, F403
