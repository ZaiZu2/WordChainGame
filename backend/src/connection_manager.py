import asyncio
from uuid import UUID

from fastapi import WebSocket

import src.models as d  # d - database
import src.schemas as s  # s - schema


class Connection:
    def __init__(self, player_id: UUID, websocket: WebSocket):
        self.player_id = player_id
        self.websocket = websocket

    def __hash__(self) -> int:
        return self.player_id.int

    def __eq__(self, other) -> bool:
        if isinstance(other, Connection):
            return self.player_id == other.player_id
        return False


class ConnectionManager:
    def __init__(self):
        # {room_id: {connection, ...}, ...}
        self.connections: dict[int, set[Connection]] = {}

    def connect(self, player_id: UUID, room_id: int, websocket: WebSocket) -> bool:
        """Return True if the connection was successful, False otherwise."""
        room_conns = self.connections.get(room_id, None)
        connection = Connection(player_id, websocket)

        if self.find_connection(player_id):
            return False
        elif room_conns is not None:
            self.connections[room_id].add(connection)
        else:
            self.connections[room_id] = {connection}
        return True

    def disconnect(self, player_id: UUID, room_id: int, websocket: WebSocket):
        room_conns = self.connections.get(room_id, None)
        conn = Connection(player_id, websocket)

        if room_conns is None:
            raise ValueError(
                'The room for which a player is trying to disconnect does not exist'
            )
        if conn not in room_conns:
            raise ValueError(
                'The player is trying to disconnect from a room they are not in'
            )

        self.connections[room_id].remove(conn)

    async def broadcast_chat_message(self, message: s.ChatMessage) -> None:
        room_conns = self.connections.get(message.room_id, None)

        if room_conns is None:
            raise ValueError(
                'The room for which a message is to be broadcasted does not exist'
            )

        websocket_message = s.WebSocketMessage(
            type=s.WebSocketMessageTypeEnum.CHAT,
            payload=message,
        )

        send_messages = [
            conn.websocket.send_json(websocket_message.model_dump_json(by_alias=True))
            for conn in room_conns
        ]
        await asyncio.gather(*send_messages)

    async def broadcast_lobby_state(self, lobby_state: s.LobbyState) -> None:
        """
        Send the lobby state to all players in the lobby. Message contains only the
        data that is due to be updated - data which is not included in the message MUST
        stay the same on the client side.
        """
        lobby_conns = self.connections.get(d.LOBBY.id_, [])

        websocket_message = s.WebSocketMessage(
            type=s.WebSocketMessageTypeEnum.LOBBY_STATE,
            payload=lobby_state,
        )

        send_messages = [
            conn.websocket.send_json(websocket_message.model_dump_json(by_alias=True))
            for conn in lobby_conns
        ]
        await asyncio.gather(*send_messages)

    async def send_lobby_state(
        self, player_id: UUID, lobby_state: s.LobbyState
    ) -> None:
        """
        Send the lobby state to a single player in the lobby. Message contains only the
        data that is due to be updated - data which is not included in the message MUST
        stay the same on the client side.
        """
        if not (conn := self.find_connection(player_id, room_id=d.LOBBY.id_)):
            raise ValueError('Player is not in the lobby')

        websocket_message = s.WebSocketMessage(
            type=s.WebSocketMessageTypeEnum.LOBBY_STATE,
            payload=lobby_state,
        )
        await conn.websocket.send_json(websocket_message.model_dump_json(by_alias=True))

    async def send_connection_state(
        self, code: int | s.CustomWebsocketCodeEnum, reason: str, websocket: WebSocket
    ) -> None:
        """
        Send a connection state message to the client, usually on connection events
        like connect, disconnect, etc. Alternative to raising a WebSocketException,
        which has inaccessible `code` and `reason` attributes to the browser.
        """
        connection_state = s.ConnectionState(code=code, reason=reason)
        websocket_message = s.WebSocketMessage(
            type=s.WebSocketMessageTypeEnum.CONNECTION_STATE,
            payload=connection_state,
        )
        await websocket.send_json(websocket_message.model_dump_json(by_alias=True))

    def find_connection(
        self,
        player_id: UUID,
        *,
        # websocket: WebSocket | None = None,
        room_id: int | None = None,
    ) -> Connection | None:
        """
        Find a connection by player_id or websocket. If `room_id` is provided, check
        for existence in a specific room.
        """
        # XOR to check that only one of the optional arguments is provided
        # if not ((player_id is None) ^ (websocket is None)):
        #     raise ValueError(
        #         'Only one of the optional arguments must be provided')

        if room_id is not None:
            room_conns = self.connections.get(room_id, None)
            if room_conns is None:
                return None

            for conn in room_conns:
                if conn.player_id == player_id:
                    return conn
        else:
            for room_conns in self.connections.values():
                for conn in room_conns:
                    if conn.player_id == player_id:
                        return conn
        return None
