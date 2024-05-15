from enum import Enum
from typing import Annotated, Literal

from pydantic import Field

import src.schemas.domain as d
import src.schemas.validation as v

# FILE STORING ONLY WEBSOCKET VALIDATION SCHEMAS USED AS WEBSOCKET INPUTS/OUTPUTS


class WebSocketMessageTypeEnum(str, Enum):
    CHAT = 'chat'  # chat messages sent by players
    GAME_STATE = 'game_state'  # issued words, scores, ...?
    LOBBY_STATE = 'lobby_state'  # available rooms, ...?
    ROOM_STATE = 'room_state'  # players in the room, ...?
    CONNECTION_STATE = 'connection_state'
    GAME_INPUT = 'game_input'  # player's input his turn
    ACTION = 'action'


#################################### GAME INPUTS ####################################


class _GameInput(v.GeneralBaseModel):
    type_: Literal[WebSocketMessageTypeEnum.GAME_INPUT] = (
        WebSocketMessageTypeEnum.GAME_INPUT
    )


class WordInput(_GameInput, v.GeneralBaseModel):
    input_type: Literal['word_input'] = Field('word_input')
    game_id: int
    word: str


# Pydantic's Discriminated Union
# https://docs.pydantic.dev/latest/concepts/unions/#discriminated-unions-with-str-discriminators
GameInput = Annotated[WordInput, Field(discriminator='input_type')]


#################################### GAME OUTPUTS ####################################


class _GameState(v.GeneralBaseModel):
    type_: Literal[WebSocketMessageTypeEnum.GAME_STATE] = (
        WebSocketMessageTypeEnum.GAME_STATE
    )


class StartGameState(_GameState, v.GeneralBaseModel):
    state: Literal[d.GameStateEnum.STARTED] = d.GameStateEnum.STARTED
    id_: int = Field(serialization_alias='id')
    status: d.GameStatusEnum
    players: list[v.GamePlayer]
    rules: v.DeathmatchRules


class EndGameState(_GameState, v.GeneralBaseModel):
    state: Literal[d.GameStateEnum.ENDED] = d.GameStateEnum.ENDED
    status: d.GameStatusEnum


class WaitState(_GameState, v.GeneralBaseModel):
    state: Literal[d.GameStateEnum.WAITING] = d.GameStateEnum.WAITING


class StartTurnState(_GameState, v.GeneralBaseModel):
    state: Literal[d.GameStateEnum.STARTED_TURN] = d.GameStateEnum.STARTED_TURN
    current_turn: v.TurnOut
    status: d.GameStatusEnum | None = None


class EndTurnState(_GameState, v.GeneralBaseModel):
    state: Literal[d.GameStateEnum.ENDED_TURN] = d.GameStateEnum.ENDED_TURN
    players: list[v.GamePlayer]
    current_turn: v.TurnOut


# Pydantic's Discriminated Union
# https://docs.pydantic.dev/latest/concepts/unions/#discriminated-unions-with-str-discriminators
GameState = Annotated[
    StartGameState | EndGameState | WaitState | StartTurnState | EndTurnState,
    Field(discriminator='state'),
]


#################################### ACTIONS ####################################


class _Action(v.GeneralBaseModel):
    type_: Literal[WebSocketMessageTypeEnum.ACTION] = WebSocketMessageTypeEnum.ACTION


class KickPlayerAction(_Action, v.GeneralBaseModel):
    action: Literal['KICK_PLAYER'] = Field('KICK_PLAYER')


Action = KickPlayerAction


#################################### OTHER MESSAGES ####################################


class Message(v.GeneralBaseModel):
    type_: Literal[WebSocketMessageTypeEnum.CHAT] = Field(
        default=WebSocketMessageTypeEnum.CHAT
    )
    id_: int | None = Field(None, serialization_alias='id')
    created_on: v.UTCDatetime | None = None
    content: str
    player_name: str
    room_id: int


class LobbyState(v.GeneralBaseModel):
    type_: Literal[WebSocketMessageTypeEnum.LOBBY_STATE] = Field(
        default=WebSocketMessageTypeEnum.LOBBY_STATE
    )
    rooms: dict[int, v.RoomOut | None] | None = None  # room_id: room
    players: dict[str, v.LobbyPlayerOut | None] | None = None  # player_name: player
    stats: v.CurrentStatistics | None = None


class RoomState(v.GeneralBaseModel):
    type_: Literal[WebSocketMessageTypeEnum.ROOM_STATE] = Field(
        default=WebSocketMessageTypeEnum.ROOM_STATE
    )
    id_: int = Field(serialization_alias='id')
    name: str
    capacity: int
    status: d.RoomStatusEnum
    rules: v.DeathmatchRules
    owner_name: str
    players: dict[str, v.RoomPlayerOut | None] | None = None  # player_name: player


class CustomWebsocketCodeEnum(int, Enum):
    MULTIPLE_CLIENTS = 4001  # Player is already connected with another client


class ConnectionState(v.GeneralBaseModel):
    type_: Literal[WebSocketMessageTypeEnum.CONNECTION_STATE] = Field(
        default=WebSocketMessageTypeEnum.CONNECTION_STATE
    )
    code: CustomWebsocketCodeEnum
    reason: str


class WebSocketMessage(v.GeneralBaseModel):
    payload: (
        Message
        | GameState
        | LobbyState
        | RoomState
        | ConnectionState
        | GameInput
        | Action
    ) = Field(discriminator='type_')
