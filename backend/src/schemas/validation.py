from pydantic import Field

import src.database as d
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


class LobbyPlayerOut(m.GeneralBaseModel):
    """Player data sent as a part of LobbyState."""

    name: str


class RoomPlayerOut(LobbyPlayerOut):
    """Player data sent as a part of RoomState."""

    ready: bool
    in_game: bool


class RoomOut(m.GeneralBaseModel):
    id_: int = Field(serialization_alias='id')
    name: str
    players_no: int
    capacity: int
    status: d.RoomStatusEnum
    rules: m.DeathmatchRules
    owner_name: str


class RoomIn(m.GeneralBaseModel):
    name: str = Field(..., max_length=10)
    capacity: int = Field(5, ge=1, le=10)
    rules: m.DeathmatchRules


class RoomInModify(m.GeneralBaseModel):
    capacity: int = Field(5, ge=1, le=10)
    rules: m.DeathmatchRules
