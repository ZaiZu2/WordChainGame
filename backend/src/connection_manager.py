import asyncio
from uuid import UUID

from fastapi import WebSocket

import src.schemas.domain as d
import src.schemas.validation as v
from src.misc import PlayerAlreadyConnectedError
from src.player_room_manager import PlayerRoomPool


class ConnectionManager:
    def __init__(self, pool: PlayerRoomPool) -> None:
        self.pool = pool

    def connect(self, player: d.Player, room_id: int) -> None:
        try:  # If successfully gets the player, it means the player is already connected
            self.pool.get_player(player.id_)
            raise PlayerAlreadyConnectedError(
                'Player is already connected with another client.'
            )
        except KeyError:
            pass

        self.pool.add_player(player, room_id)

    def disconnect(self, player_id: UUID):
        if not self.pool.get_player(player_id):
            raise ValueError('Player is not connected')
        self.pool.remove_player(player_id)

    async def broadcast_chat_message(self, message: v.Message) -> None:
        room_players = self.pool.get_room_players(message.room_id)
        if room_players is None:
            raise ValueError('Room does not exist')

        websocket_message = v.WebSocketMessage(payload=message)
        message_json = websocket_message.model_dump_json(by_alias=True)
        send_messages = [
            player.websocket.send_json(message_json) for player in room_players
        ]
        await asyncio.gather(*send_messages)

    async def send_chat_message(
        self,
        message: v.Message,
        player_id: UUID,
    ) -> None:
        player = self.pool.get_player(player_id)
        if player is None:
            raise ValueError('Player is not connected')

        websocket_message = v.WebSocketMessage(payload=message)
        await player.websocket.send_json(
            websocket_message.model_dump_json(by_alias=True)
        )

    async def broadcast_lobby_state(self, lobby_state: v.LobbyState) -> None:
        """
        Send the lobby state to all players in the lobby. Message contains only the data
        that is due to be updated/removed (if set to None) - data which is not included
        in the message MUST stay the same on the client side.
        """
        lobby_players = self.pool.get_room_players(d.LOBBY.id_)

        websocket_message = v.WebSocketMessage(payload=lobby_state)
        message_json = websocket_message.model_dump_json(by_alias=True)
        send_messages = [
            player.websocket.send_json(message_json) for player in lobby_players
        ]
        await asyncio.gather(*send_messages)

    async def send_lobby_state(
        self, player_id: UUID, lobby_state: v.LobbyState
    ) -> None:
        """
        Send the lobby state to a single player in the lobby. Message contains only the
        data that is due to be updated - data which is not included in the message MUST
        stay the same on the client side.
        """
        player = self.pool.get_player(player_id)
        if player is None:
            raise ValueError('Player is not connected')

        websocket_message = v.WebSocketMessage(payload=lobby_state)
        await player.websocket.send_json(
            websocket_message.model_dump_json(by_alias=True)
        )

    async def broadcast_room_state(self, room_id: int, room_state: v.RoomState) -> None:
        """
        Send the room state to all players in the room. Message contains only the data
        that is due to be updated/removed (if set to None) - data which is not included
        in the message MUST stay the same on the client side.
        """
        room_players = self.pool.get_room_players(room_id)
        if room_players is None:
            raise ValueError('Room does not exist')

        websocket_message = v.WebSocketMessage(payload=room_state)
        message_json = websocket_message.model_dump_json(by_alias=True)
        send_messages = [
            player.websocket.send_json(message_json) for player in room_players
        ]
        await asyncio.gather(*send_messages)

    async def broadcast_game_state(self, room_id: int, game_state: v.GameState) -> None:
        """Send the game state to all players in the room."""
        room_players = self.pool.get_room_players(room_id)
        if room_players is None:
            raise ValueError('Room does not exist')

        websocket_message = v.WebSocketMessage(payload=game_state)
        message_json = websocket_message.model_dump_json(by_alias=True)
        send_messages = [
            player.websocket.send_json(message_json) for player in room_players
        ]
        await asyncio.gather(*send_messages)

    async def send_connection_state(
        self, code: v.CustomWebsocketCodeEnum, reason: str, websocket: WebSocket
    ) -> None:
        """
        Send a connection state message to the client, usually on connection events
        like connect, disconnect, etc. Alternative to raising a WebSocketException,
        which has inaccessible `code` and `reason` attributes to the browser.
        """
        connection_state = v.ConnectionState(code=code, reason=reason)
        websocket_message = v.WebSocketMessage(payload=connection_state)
        await websocket.send_json(websocket_message.model_dump_json(by_alias=True))

    def move_player(self, player_id: UUID, from_room_id: int, to_room_id: int) -> None:
        """Move a player's websocket connection from one room to another."""
        if not (self.pool.get_room(player_id=player_id).id_ == from_room_id):
            raise ValueError('Player is not in the specified room')
        if not self.pool.does_room_exist(to_room_id):
            raise ValueError('Room to move the player to does not exist')

        player = self.pool.get_player(player_id)
        self.pool.remove_player(player_id)
        player.ready = False
        player.in_game = False
        self.pool.add_player(player, to_room_id)

    async def send_action(self, action: v.Action, player_id: UUID) -> None:
        player = self.pool.get_player(player_id)
        if player is None:
            raise ValueError('Player is not connected')

        websocket_message = v.WebSocketMessage(payload=action)
        await player.websocket.send_json(
            websocket_message.model_dump_json(by_alias=True)
        )
