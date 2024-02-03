from functools import lru_cache
from uuid import UUID

from fastapi import WebSocket


class Connection:
    def __init__(self, player_id: UUID, connection: WebSocket):
        self.player_id = player_id
        self.connection = connection


class ConnectionManager:
    def __init__(self):
        self.connections: dict[int, set[Connection]] = {}

    def add_connection(self, player_id: UUID, game_id: int, conn: WebSocket):
        room_conns = self.connections.get(game_id, None)
        if room_conns is not None:
            conn = Connection(player_id, conn)
            self.connections[room_conns].add(conn)
        else:
            self.connections[game_id] = set(Connection(player_id, conn))

    def remove_connection(self, player_id: UUID, game_id: int, conn: WebSocket):
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

    async def broadcast(self, game_id: int, message: str):
        room_conns = self.connections.get(game_id, None)

        if room_conns is None:
            raise ValueError(
                'The room for which a player is trying to broadcast does not exist'
            )

        for conn in room_conns:
            await conn.connection.send_text(message)


@lru_cache
def get_connection_manager() -> ConnectionManager:
    """FastAPI dependency injection function to pass a ConnectionManager instance."""
    return ConnectionManager()
