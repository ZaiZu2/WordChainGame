from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

import src.models as d


class GeneralBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class MePlayer(GeneralBaseModel):
    id_: UUID = Field(serialization_alias='id')
    name: str
    created_on: datetime


class RoomOut(GeneralBaseModel):
    id_: int = Field(serialization_alias='id')
    name: str
    players_no: int
    capacity: int
    status: d.RoomStatusEnum
    rules: dict


class RoomIn(GeneralBaseModel):
    name: str
    rules: dict


class WebSocketMessageTypeEnum(str, Enum):
    CHAT = 'chat'  # chat messages sent by players
    GAME_STATE = 'game_state'  # issued words, scores, ...?
    LOBBY_STATE = 'lobby_state'  # available rooms, ...?
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


class LobbyState(GeneralBaseModel):
    rooms: dict[int, RoomOut]  # room_id: room


class RoomState(GeneralBaseModel):
    pass


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
            WebSocketMessageTypeEnum.CONNECTION_STATE: ConnectionState,
        }

        expected_payload_type = payload_types.get(message.type)
        if not isinstance(message.payload, expected_payload_type):
            raise ValueError(
                f'Wrong payload provided for the {message.type} message type'
            )
