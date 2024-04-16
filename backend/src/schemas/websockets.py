from enum import Enum
from typing import Literal

from pydantic import Field, model_validator

import src.models as d
import src.schemas.general as s

#################################### GAME INPUTS ####################################


class GameInput(s.GeneralBaseModel):
    game_id: int
    word: str


#################################### GAME OUTPUTS ####################################


class StartGameState(s.GeneralBaseModel):
    type_: Literal['start_game'] = Field('start_game', serialization_alias='type')
    id_: int = Field(serialization_alias='id')
    status: d.GameStatusEnum
    players: list[s.GamePlayer]
    lost_players: list[s.GamePlayer]
    rules: s.DeathmatchRules


class EndGameState(s.GeneralBaseModel):
    type_: Literal['end_game'] = Field('end_game', serialization_alias='type')
    status: d.GameStatusEnum


class StartTurnState(s.GeneralBaseModel):
    type_: Literal['start_turn'] = Field('start_turn', serialization_alias='type')
    current_turn: s.Turn
    status: d.GameStatusEnum | None = None


class EndTurnState(s.GeneralBaseModel):
    type_: Literal['end_turn'] = Field('end_turn', serialization_alias='type')
    players: list[s.GamePlayer]
    lost_players: list[s.GamePlayer]
    current_turn: s.Turn


GameState = StartGameState | EndGameState | StartTurnState | EndTurnState

# Unnecessary discriminator as game state is not sent by the client.
# class _GameState(s.GeneralBaseModel):
#     state: GameState = Field(..., serialization_alias='type', discriminator='type_')


#################################### OTHER MESSAGES ####################################


class LobbyState(s.GeneralBaseModel):
    rooms: dict[int, s.RoomOut | None] | None = None  # room_id: room
    players: dict[str, s.LobbyPlayerOut | None] | None = None  # player_name: player
    stats: s.CurrentStatistics | None = None


class RoomState(s.GeneralBaseModel):
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
    code: CustomWebsocketCodeEnum
    reason: str


class WebSocketMessageTypeEnum(str, Enum):
    CHAT = 'chat'  # chat messages sent by players
    GAME_STATE = 'game_state'  # issued words, scores, ...?
    GAME_INPUT = 'game_input'  # player's input his turn
    LOBBY_STATE = 'lobby_state'  # available rooms, ...?
    ROOM_STATE = 'room_state'  # players in the room, ...?
    CONNECTION_STATE = 'connection_state'


class WebSocketMessage(s.GeneralBaseModel):
    type: WebSocketMessageTypeEnum
    payload: (
        s.ChatMessage | GameState | GameInput | LobbyState | RoomState | ConnectionState
    )

    @model_validator(mode='after')
    @classmethod
    def _check_corresponding_payload(cls, message: 'WebSocketMessage'):
        payload_types: dict[str, list[type[s.GeneralBaseModel]]] = {
            WebSocketMessageTypeEnum.CHAT: [s.ChatMessage],
            WebSocketMessageTypeEnum.GAME_STATE: [
                StartGameState,
                EndGameState,
                StartTurnState,
                EndTurnState,
            ],
            WebSocketMessageTypeEnum.GAME_INPUT: [GameInput],
            WebSocketMessageTypeEnum.LOBBY_STATE: [LobbyState],
            WebSocketMessageTypeEnum.ROOM_STATE: [RoomState],
            WebSocketMessageTypeEnum.CONNECTION_STATE: [ConnectionState],
        }

        expected_payload_type = payload_types.get(message.type)

        if expected_payload_type is None:
            raise ValueError(f'Unexpected message type: {message.type}')
        elif type(message.payload) not in expected_payload_type:
            raise ValueError(
                f'Wrong payload provided for the {message.type} message type'
            )
