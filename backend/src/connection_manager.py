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
        self.connections: dict[int, set[Connection]] = {}

    def connect(self, player_id: UUID, room_id: int, websocket: WebSocket) -> bool:
        """Return True if the connection was successful, False otherwise."""
        room_conns = self.connections.get(room_id, None)
        connection = Connection(player_id, websocket)

        if self.find_connection(player_id=player_id):
            return False
        elif room_conns is not None:
            self.connections[room_id].add(connection)
        else:
            self.connections[room_id] = {connection}
        return True

    def disconnect(self, player_id: UUID, room_id: int, websocket: WebSocket):
        room_conns = self.connections.get(room_id, None)
        connection = Connection(player_id, websocket)

        if room_conns is None:
            raise ValueError(
                'The room for which a player is trying to disconnect does not exist'
            )
        if connection not in room_conns:
            raise ValueError(
                'The player is trying to disconnect from a room they are not in'
            )

        self.connections[room_id].remove(connection)

    async def broadcast_chat_message(self, message: d.Message) -> None:
        room_conns = self.connections.get(message.room_id, None)

        if room_conns is None:
            raise ValueError(
                'The room for which a message is to be broadcasted does not exist'
            )

        chat_message = s.ChatMessage(
            id_=message.id_,
            player_name=message.player.name,
            room_id=message.room_id,
            content=message.content,
            created_on=message.created_on,
        )
        websocket_message = s.WebSocketMessage(
            type=s.WebSocketMessageTypeEnum.CHAT,
            payload=chat_message,
        )

        send_messages = [
            conn.websocket.send_json(websocket_message.model_dump_json(by_alias=True))
            for conn in room_conns
        ]
        await asyncio.gather(*send_messages)

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
        self, player_id: UUID | None = None, websocket: WebSocket | None = None
    ) -> Connection | None:
        """Find a connection by player_id or websocket."""
        # XOR to check that only one of the optional arguments is provided
        if not ((player_id is None) ^ (websocket is None)):
            raise ValueError('Only one of the optional arguments must be provided')

        if player_id is not None:
            for room_conns in self.connections.values():
                for conn in room_conns:
                    if conn.player_id == player_id:
                        return conn
        else:
            for room_conns in self.connections.values():
                for conn in room_conns:
                    if conn.websocket == websocket:
                        return conn
        return None
