from functools import lru_cache
from uuid import UUID

from fastapi import WebSocket

import src.models as d  # d - database
import src.schemas as s  # s - schema


class Connection:
    def __init__(self, player_id: UUID, connection: WebSocket):
        self.player_id = player_id
        self.connection = connection

    def __hash__(self) -> int:
        return self.player_id.int

    def __eq__(self, other) -> bool:
        if isinstance(other, Connection):
            return self.player_id == other.player_id
        return False


class ConnectionManager:
    def __init__(self):
        self.connections: dict[int, set[Connection]] = {}

    def connect(self, player_id: UUID, room_id: int, conn: WebSocket):
        room_conns = self.connections.get(room_id, None)
        if room_conns is not None:
            conn = Connection(player_id, conn)
            self.connections[room_id].add(conn)
        else:
            self.connections[room_id] = {Connection(player_id, conn)}

    def disconnect(self, player_id: UUID, room_id: int, conn: WebSocket):
        room_conns = self.connections.get(room_id, None)
        conn = Connection(player_id, conn)

        if room_conns is None:
            raise ValueError(
                'The room for which a player is trying to disconnect does not exist'
            )
        if conn not in room_conns:
            raise ValueError(
                'The player is trying to disconnect from a room they are not in'
            )

        self.connections[room_id].remove(conn)

    async def broadcast_chat_message(self, message: d.Message) -> None:
        """Brodcast a chat message - by default it's a 'root' message to the 'lobby' room."""
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
            type=s.WebSocketMessageType.CHAT,
            payload=chat_message,
        )
        for conn in room_conns:
            await conn.connection.send_json(
                websocket_message.model_dump_json(by_alias=True)
            )


@lru_cache
def get_connection_manager() -> ConnectionManager:
    """FastAPI dependency injection function to pass a ConnectionManager instance into endpoints."""
    return ConnectionManager()
