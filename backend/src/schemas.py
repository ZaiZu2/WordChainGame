from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class GeneralBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class MePlayer(GeneralBaseModel):
    id_: UUID = Field(serialization_alias='id')
    name: str
    created_on: datetime


class Room(GeneralBaseModel):
    id_: int = Field(serialization_alias='id')
    name: str
    rules: dict


class NewRoom(GeneralBaseModel):
    name: str
    rules: dict


class WebSocketMessageType(str, Enum):
    CHAT = 'chat'  # chat messages sent by players
    GAME_STATE = 'game_state'  # issued words, scores, ...?
    LOBBY_STATE = 'lobby_state'  # available rooms, ...?


class ChatMessage(GeneralBaseModel):
    id_: int | None = Field(None, serialization_alias='id')
    created_on: datetime | None = None
    content: str
    player_name: str
    room_id: int


class GameState(GeneralBaseModel):
    pass


class LobbyState(GeneralBaseModel):
    rooms: list[Room]


class WebSocketMessage(GeneralBaseModel):
    type: WebSocketMessageType
    payload: ChatMessage | GameState | LobbyState

    @model_validator(mode='after')
    @classmethod
    def _check_corresponding_payload(cls, message: 'WebSocketMessage'):
        if message.type == WebSocketMessageType.CHAT and not isinstance(
            message.payload, ChatMessage
        ):
            raise ValueError(
                f'Wrong payload provided for the {message.type} message type'
            )
        elif message.type == WebSocketMessageType.GAME_STATE and not isinstance(
            message.payload, GameState
        ):
            raise ValueError(
                f'Wrong payload provided for the {message.type} message type'
            )
        elif message.type == WebSocketMessageType.LOBBY_STATE and not isinstance(
            message.payload, LobbyState
        ):
            raise ValueError(
                f'Wrong payload provided for the {message.type} message type'
            )
