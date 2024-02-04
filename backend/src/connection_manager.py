from functools import lru_cache
from uuid import UUID

from fastapi import WebSocket

import src.schemas as s  # s - schema


class Connection:
    def __init__(self, player_id: UUID, connection: WebSocket):
        self.player_id = player_id
        self.connection = connection


class ConnectionManager:
    def __init__(self):
        self.connections: dict[int, set[Connection]]

    def connect(self, player_id: UUID, game_id: int, conn: WebSocket):
        room_conns = self.connections.get(game_id, None)
        if room_conns is not None:
            conn = Connection(player_id, conn)
            self.connections[room_conns].add(conn)
        else:
            self.connections[game_id] = set(Connection(player_id, conn))

    def disconnect(self, player_id: UUID, game_id: int, conn: WebSocket):
        room_conns = self.connections.get(game_id, None)
        conn = Connection(player_id, conn)

        if room_conns is None:
            raise ValueError(
                'The room for which a player is trying to disconnect does not exist'
            )
        if conn not in room_conns:
            raise ValueError(
                'The player is trying to disconnect from a room they are not in'
            )

        self.connections[room_conns].remove(conn)

    async def broadcast_chat_message(
        self, chat_message: str, /, player_name: str = 'root', room_id: int = 0
    ):
        """Brodcast a chat message - by default it's a 'root' message to the 'lobby' room."""
        room_conns = self.connections.get(room_id, None)

        if room_conns is None:
            raise ValueError(
                'The room for which a message is to be broadcasted does not exist'
            )

        chat_message = s.ChatMessage(
            player_name=player_name,
            room_id=room_id,
            content=chat_message,
        )
        websocket_message = s.WebSocketMessage(
            type=s.WebSocketMessageType.CHAT,
            payload=chat_message,
        )
        for conn in room_conns:
            await conn.connection.send_json(websocket_message.model_dump())


@lru_cache
def get_connection_manager() -> ConnectionManager:
    """FastAPI dependency injection function to pass a ConnectionManager instance into endpoints."""
    return ConnectionManager()
