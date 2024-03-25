from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

import src.models as d


class GeneralBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class MePlayer(GeneralBaseModel):
    id_: UUID = Field(serialization_alias='id')
    name: str
    created_on: datetime


class PlayerOut(GeneralBaseModel):
    name: str
    created_on: datetime


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


class RoomOut(GeneralBaseModel):
    id_: int = Field(serialization_alias='id')
    name: str
    players_no: int
    capacity: int
    status: d.RoomStatusEnum
    rules: DeathmatchRules
    owner_name: str


class RoomIn(GeneralBaseModel):
    name: str
    capacity: int = Field(5, ge=1, le=10)
    rules: DeathmatchRules


class WebSocketMessageTypeEnum(str, Enum):
    CHAT = 'chat'  # chat messages sent by players
    GAME_STATE = 'game_state'  # issued words, scores, ...?
    LOBBY_STATE = 'lobby_state'  # available rooms, ...?
    ROOM_STATE = 'room_state'  # players in the room, ...?
    CONNECTION_STATE = 'connection_state'


class ChatMessage(GeneralBaseModel):
    id_: int | None = Field(None, serialization_alias='id')
    created_on: datetime | None = None
    content: str
    player_name: str
    room_id: int


class CustomWebsocketCodeEnum(int, Enum):
    MULTIPLE_CLIENTS = 4001  # Player is already connected with another client


class ConnectionState(GeneralBaseModel):
    code: CustomWebsocketCodeEnum
    reason: str


class CurrentStatistics(GeneralBaseModel):
    active_players: int
    active_rooms: int


class AllTimeStatistics(GeneralBaseModel):
    longest_chain: int
    longest_game_time: int
    total_games: int


class LobbyState(GeneralBaseModel):
    rooms: dict[int, RoomOut | None] | None = None  # room_id: room
    players: dict[str, PlayerOut | None] | None = None  # player_name: player
    stats: CurrentStatistics | None = None


class RoomState(GeneralBaseModel):
    id_: int = Field(serialization_alias='id')
    name: str
    capacity: int
    status: d.RoomStatusEnum
    rules: DeathmatchRules
    owner_name: str
    players: dict[str, PlayerOut | None] | None = None  # player_name: player


class GameState(GeneralBaseModel):
    pass


class WebSocketMessage(GeneralBaseModel):
    type: WebSocketMessageTypeEnum
    payload: ChatMessage | GameState | LobbyState | RoomState | ConnectionState

    @model_validator(mode='after')
    @classmethod
    def _check_corresponding_payload(cls, message: 'WebSocketMessage'):
        payload_types = {
            WebSocketMessageTypeEnum.CHAT: ChatMessage,
            WebSocketMessageTypeEnum.GAME_STATE: GameState,
            WebSocketMessageTypeEnum.LOBBY_STATE: LobbyState,
            WebSocketMessageTypeEnum.ROOM_STATE: RoomState,
            WebSocketMessageTypeEnum.CONNECTION_STATE: ConnectionState,
        }

        expected_payload_type = payload_types.get(message.type)
        if not isinstance(message.payload, expected_payload_type):
            raise ValueError(
                f'Wrong payload provided for the {message.type} message type'
            )
