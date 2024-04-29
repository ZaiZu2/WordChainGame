from enum import Enum
from typing import Annotated, Literal

from pydantic import Field

import src.database as d
import src.schemas as s

# FILE STORING ONLY WEBSOCKET VALIDATION SCHEMAS USED AS WEBSOCKET INPUTS/OUTPUTS


class WebSocketMessageTypeEnum(str, Enum):
    CHAT = 'chat'  # chat messages sent by players
    GAME_STATE = 'game_state'  # issued words, scores, ...?
    GAME_INPUT = 'game_input'  # player's input his turn
    LOBBY_STATE = 'lobby_state'  # available rooms, ...?
    ROOM_STATE = 'room_state'  # players in the room, ...?
    CONNECTION_STATE = 'connection_state'


#################################### GAME INPUTS ####################################


class _GameInput(s.GeneralBaseModel):
    type_: Literal[WebSocketMessageTypeEnum.GAME_INPUT] = (
        WebSocketMessageTypeEnum.GAME_INPUT
    )


class WordInput(_GameInput, s.GeneralBaseModel):
    input_type: Literal['word_input'] = Field('word_input')
    game_id: int
    word: str


# Pydantic's Discriminated Union
# https://docs.pydantic.dev/latest/concepts/unions/#discriminated-unions-with-str-discriminators
GameInput = Annotated[WordInput, Field(discriminator='input_type')]

#################################### GAME OUTPUTS ####################################


class _GameState(s.GeneralBaseModel):
    type_: Literal[WebSocketMessageTypeEnum.GAME_STATE] = (
        WebSocketMessageTypeEnum.GAME_STATE
    )


class StartGameState(_GameState, s.GeneralBaseModel):
    state: Literal[s.GameStateEnum.STARTING] = s.GameStateEnum.STARTING
    id_: int = Field(serialization_alias='id')
    status: d.GameStatusEnum
    players: list[s.GamePlayer]
    rules: s.DeathmatchRules


class EndGameState(_GameState, s.GeneralBaseModel):
    state: Literal[s.GameStateEnum.ENDING] = s.GameStateEnum.ENDING
    status: d.GameStatusEnum


class WaitState(_GameState, s.GeneralBaseModel):
    state: Literal[s.GameStateEnum.WAITING] = s.GameStateEnum.WAITING


class StartTurnState(_GameState, s.GeneralBaseModel):
    state: Literal[s.GameStateEnum.START_TURN] = s.GameStateEnum.START_TURN
    current_turn: s.TurnOut
    status: d.GameStatusEnum | None = None


class EndTurnState(_GameState, s.GeneralBaseModel):
    state: Literal[s.GameStateEnum.END_TURN] = s.GameStateEnum.END_TURN
    players: list[s.GamePlayer]
    current_turn: s.TurnOut


# Pydantic's Discriminated Union
# https://docs.pydantic.dev/latest/concepts/unions/#discriminated-unions-with-str-discriminators
GameState = Annotated[
    StartGameState | EndGameState | WaitState | StartTurnState | EndTurnState,
    Field(discriminator='state'),
]


#################################### OTHER MESSAGES ####################################


class ChatMessage(s.GeneralBaseModel):
    type_: Literal[WebSocketMessageTypeEnum.CHAT] = Field(
        default=WebSocketMessageTypeEnum.CHAT
    )
    id_: int | None = Field(None, serialization_alias='id')
    created_on: s.UTCDatetime | None = None
    content: str
    player_name: str
    room_id: int


class LobbyState(s.GeneralBaseModel):
    type_: Literal[WebSocketMessageTypeEnum.LOBBY_STATE] = Field(
        default=WebSocketMessageTypeEnum.LOBBY_STATE
    )
    rooms: dict[int, s.RoomOut | None] | None = None  # room_id: room
    players: dict[str, s.LobbyPlayerOut | None] | None = None  # player_name: player
    stats: s.CurrentStatistics | None = None


class RoomState(s.GeneralBaseModel):
    type_: Literal[WebSocketMessageTypeEnum.ROOM_STATE] = Field(
        default=WebSocketMessageTypeEnum.ROOM_STATE
    )
    id_: int = Field(serialization_alias='id')
    name: str
    capacity: int
    status: d.RoomStatusEnum
    rules: s.DeathmatchRules
    owner_name: str
    players: dict[str, s.RoomPlayerOut | None] | None = None  # player_name: player


class CustomWebsocketCodeEnum(int, Enum):
    MULTIPLE_CLIENTS = 4001  # Player is already connected with another client


class ConnectionState(s.GeneralBaseModel):
    type_: Literal[WebSocketMessageTypeEnum.CONNECTION_STATE] = Field(
        default=WebSocketMessageTypeEnum.CONNECTION_STATE
    )
    code: CustomWebsocketCodeEnum
    reason: str


class WebSocketMessage(s.GeneralBaseModel):
    payload: (
        ChatMessage | GameState | GameInput | LobbyState | RoomState | ConnectionState
    ) = Field(discriminator='type_')
