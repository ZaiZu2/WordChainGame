from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

import src.models as d  # d - database


class GeneralBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class MePlayer(GeneralBaseModel):
    id_: UUID = Field(alias='id')
    name: str
    created_on: datetime


class Room(GeneralBaseModel):
    id_: int = Field(alias='id')
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
    player_name: str
    room_id: int
    created_on: datetime = Field(default_factory=datetime.now)
    content: str


class GameStateMessage(GeneralBaseModel):
    pass


class LobbyState(GeneralBaseModel):
    rooms: list[Room]


class WebSocketMessage(GeneralBaseModel):
    type: WebSocketMessageType
    payload: ChatMessage | GameStateMessage | LobbyState

    @model_validator(mode='after')
    @classmethod
    def _check_corresponding_payload(cls, message: 'WebSocketMessage'):
        if message.type == WebSocketMessageType.CHAT:
            assert isinstance(message.payload, ChatMessage)
        elif message.type == WebSocketMessageType.GAME_STATE:
            assert isinstance(message.payload, GameStateMessage)
        elif message.type == WebSocketMessageType.LOBBY_STATE:
            assert isinstance(message.payload, LobbyState)
