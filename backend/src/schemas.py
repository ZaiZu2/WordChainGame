from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


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


class ChatMessageIn(GeneralBaseModel):
    content: str
    player_name: str
    room_id: int


class ChatMessageOut(ChatMessageIn):
    # message_id: int # TODO: To be provided by the database
    created_on: datetime = Field(
        default_factory=datetime.now
    )  # TODO: Remove any default values


class GameState(GeneralBaseModel):
    pass


class LobbyState(GeneralBaseModel):
    rooms: list[Room]


class WebSocketMessage(GeneralBaseModel):
    type: WebSocketMessageType
    payload: ChatMessageIn | GameState | LobbyState

    @model_validator(mode='after')
    @classmethod
    def _check_corresponding_payload(cls, message: 'WebSocketMessage'):
        if message.type == WebSocketMessageType.CHAT and not isinstance(
            message.payload, ChatMessageIn
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
