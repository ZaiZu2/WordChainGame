import asyncio
from uuid import UUID

from fastapi import WebSocket, WebSocketException

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

    def connect(self, player_id: UUID, room_id: int, websocket_conn: WebSocket):
        room_conns = self.connections.get(room_id, None)
        player_conn = Connection(player_id, websocket_conn)

        if room_conns is not None and player_conn in room_conns:
            raise WebSocketException(
                4001,
                'Player can use only one client at a time. Disconnect the previous one first.',
            )
        elif room_conns is not None:
            self.connections[room_id].add(player_conn)
        else:
            self.connections[room_id] = {player_conn}

    def disconnect(self, player_id: UUID, room_id: int, websocket_conn: WebSocket):
        room_conns = self.connections.get(room_id, None)
        player_conn = Connection(player_id, websocket_conn)

        if room_conns is None:
            raise ValueError(
                'The room for which a player is trying to disconnect does not exist'
            )
        if player_conn not in room_conns:
            raise ValueError(
                'The player is trying to disconnect from a room they are not in'
            )

        self.connections[room_id].remove(player_conn)

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

        send_messages = [
            conn.connection.send_json(websocket_message.model_dump_json(by_alias=True))
            for conn in room_conns
        ]
        await asyncio.gather(*send_messages)
