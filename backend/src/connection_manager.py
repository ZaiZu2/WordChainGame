import asyncio
from collections import namedtuple
from uuid import UUID

from fastapi import WebSocket

import src.schemas as s  # s - schema
import src.schemas.domain as m
from src.error_handlers import PlayerAlreadyConnectedError


class ConnectionPool:
    PlayerInfo = namedtuple('PlayerInfo', ['conn', 'room_id'])

    def __init__(self) -> None:
        # {
        #     room_id: m.Room,
        #     ...
        # }
        self._room_map: dict[int, m.Room] = {m.LOBBY.id_: m.LOBBY}
        # {
        #     player_id: (Connection, room_id),
        #     ...
        # }
        self._player_map: dict[UUID, ConnectionPool.PlayerInfo] = {}

    @property
    def active_players(self) -> int:
        return len(self._player_map)

    @property
    def active_rooms(self) -> int:
        return len(self._room_map) - 1

    def get_conn(self, player_id: UUID) -> m.Player | None:
        if not (player_info := self._player_map.get(player_id, None)):
            return None
        return player_info.conn

    def get_room(
        self, *, room_id: int | None = None, player_id: UUID | None = None
    ) -> m.Room | None:
        if not (bool(room_id) ^ bool(player_id)):
            raise ValueError('Either room_id or player_id must be provided')

        room_info = None
        if room_id:
            room_info = self._room_map.get(room_id, None)
        elif player_id:
            player_info = self._player_map.get(player_id, None)
            room_id = player_info.room_id
            room_info = self._room_map.get(room_id, None)

        return room_info

    def get_room_conns(self, room_id: int) -> set[m.Player]:
        room_conns = self._room_map[room_id].conns
        return set(room_conns.values())

    def add(self, conn: m.Player, room_id: int) -> None:
        # TODO: Should the room be implicitly created if it doesn't exist?
        if room_id in self._room_map:
            self._room_map[room_id].conns[conn.id_] = conn
        else:
            self._room_map[room_id].conns = {conn.id_: conn}

        self._player_map[conn.id_] = ConnectionPool.PlayerInfo(conn, room_id)

    def remove(self, player_id: UUID) -> None:
        player_info = self._player_map.pop(player_id)
        room_id = player_info.room_id
        self._room_map[room_id].conns.pop(player_id)

    def exists(self, room_id: int) -> bool:
        return room_id in self._room_map

    def create_room(self, room_id: int) -> None:
        if self.exists(room_id):
            raise ValueError('Room already exists')
        self._room_map[room_id] = m.Room(room_id)


class ConnectionManager:
    def __init__(self) -> None:
        self.pool = ConnectionPool()

    def connect(self, player: m.Player, room_id: int):
        if self.pool.get_conn(player.id_):
            raise PlayerAlreadyConnectedError(
                'Player is already connected with another client.'
            )

        self.pool.add(player, room_id)

    def disconnect(self, player_id: UUID):
        if not self.pool.get_conn(player_id):
            raise ValueError('Player is not connected')
        self.pool.remove(player_id)

    async def broadcast_chat_message(self, message: s.ChatMessage) -> None:
        room_conns = self.pool.get_room_conns(message.room_id)
        if room_conns is None:
            raise ValueError('Room does not exist')

        websocket_message = s.WebSocketMessage(payload=message)
        message_json = websocket_message.model_dump_json(by_alias=True)
        send_messages = [conn.websocket.send_json(message_json) for conn in room_conns]
        await asyncio.gather(*send_messages)

    async def send_chat_message(
        self,
        message: s.ChatMessage,
        player_id: UUID,
    ) -> None:
        conn = self.pool.get_conn(player_id)
        if conn is None:
            raise ValueError('Player is not connected')

        websocket_message = s.WebSocketMessage(payload=message)
        await conn.websocket.send_json(websocket_message.model_dump_json(by_alias=True))

    async def broadcast_lobby_state(self, lobby_state: s.LobbyState) -> None:
        """
        Send the lobby state to all players in the lobby. Message contains only the data
        that is due to be updated/removed (if set to None) - data which is not included
        in the message MUST stay the same on the client side.
        """
        lobby_conns = self.pool.get_room_conns(m.LOBBY.id_)

        websocket_message = s.WebSocketMessage(payload=lobby_state)
        message_json = websocket_message.model_dump_json(by_alias=True)
        send_messages = [conn.websocket.send_json(message_json) for conn in lobby_conns]
        await asyncio.gather(*send_messages)

    async def send_lobby_state(
        self, player_id: UUID, lobby_state: s.LobbyState
    ) -> None:
        """
        Send the lobby state to a single player in the lobby. Message contains only the
        data that is due to be updated - data which is not included in the message MUST
        stay the same on the client side.
        """
        conn = self.pool.get_conn(player_id)
        if conn is None:
            raise ValueError('Player is not connected')

        websocket_message = s.WebSocketMessage(payload=lobby_state)
        await conn.websocket.send_json(websocket_message.model_dump_json(by_alias=True))

    async def broadcast_room_state(self, room_id: int, room_state: s.RoomState) -> None:
        """
        Send the room state to all players in the room. Message contains only the data
        that is due to be updated/removed (if set to None) - data which is not included
        in the message MUST stay the same on the client side.
        """
        room_conns = self.pool.get_room_conns(room_id)
        if room_conns is None:
            raise ValueError('Room does not exist')

        websocket_message = s.WebSocketMessage(payload=room_state)
        message_json = websocket_message.model_dump_json(by_alias=True)
        send_messages = [conn.websocket.send_json(message_json) for conn in room_conns]
        await asyncio.gather(*send_messages)

    async def broadcast_game_state(self, room_id: int, game_state: s.GameState) -> None:
        """Send the game state to all players in the room."""
        room_conns = self.pool.get_room_conns(room_id)
        if room_conns is None:
            raise ValueError('Room does not exist')

        websocket_message = s.WebSocketMessage(payload=game_state)
        message_json = websocket_message.model_dump_json(by_alias=True)
        send_messages = [conn.websocket.send_json(message_json) for conn in room_conns]
        await asyncio.gather(*send_messages)

    async def send_connection_state(
        self, code: s.CustomWebsocketCodeEnum, reason: str, websocket: WebSocket
    ) -> None:
        """
        Send a connection state message to the client, usually on connection events
        like connect, disconnect, etc. Alternative to raising a WebSocketException,
        which has inaccessible `code` and `reason` attributes to the browser.
        """
        connection_state = s.ConnectionState(code=code, reason=reason)
        websocket_message = s.WebSocketMessage(payload=connection_state)
        await websocket.send_json(websocket_message.model_dump_json(by_alias=True))

    def move_player(self, player_id: UUID, from_room_id: int, to_room_id: int) -> None:
        """Move a player's websocket connection from one room to another."""
        if not (self.pool.get_room(player_id=player_id).id_ == from_room_id):
            raise ValueError('Player is not in the specified room')
        if not self.pool.exists(to_room_id):
            raise ValueError('Room to move the player to does not exist')

        conn = self.pool.get_conn(player_id)
        self.pool.remove(player_id)
        conn.ready = False
        conn.in_game = False
        self.pool.add(conn, to_room_id)

    async def send_action(self, action: s.Action, player_id: UUID) -> None:
        conn = self.pool.get_conn(player_id)
        if conn is None:
            raise ValueError('Player is not connected')

        websocket_message = s.WebSocketMessage(payload=action)
        await conn.websocket.send_json(websocket_message.model_dump_json(by_alias=True))
