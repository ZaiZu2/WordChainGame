from collections import namedtuple
from uuid import UUID

import src.schemas.domain as m


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
