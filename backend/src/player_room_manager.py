from uuid import UUID

import src.schemas.domain as m


class PlayerRoomManager:
    """Manages players and rooms currently active in the game."""

    def __init__(self) -> None:
        self._room_map: dict[int, m.Room] = {m.LOBBY.id_: m.LOBBY}
        self._player_map: dict[UUID, m.Player] = {}

    @property
    def active_players(self) -> int:
        return len(self._player_map)

    @property
    def active_rooms(self) -> int:
        return len(self._room_map) - 1

    def get_player(self, player_id: UUID) -> m.Player | None:
        return self._player_map.get(player_id, None)

    def get_room(
        self, *, room_id: int | None = None, player_id: UUID | None = None
    ) -> m.Room | None:
        """Find a room by it's ID or the player who's inside it."""
        if not (bool(room_id) ^ bool(player_id)):
            raise ValueError('Either room_id or player_id must be provided')

        if room_id:
            return self._room_map.get(room_id, None)
        else:
            player = self._player_map.get(player_id, None)
            return player.room

    def get_room_players(self, room_id: int) -> set[m.Player]:
        room_players = self._room_map[room_id].players
        return set(room_players.values())

    def add(self, player: m.Player, room_id: int) -> None:
        # TODO: Should the room be implicitly created if it doesn't exist?
        room = self.get_room(room_id=room_id)
        player.room = room
        self._player_map[player.id_] = player
        self._room_map[room_id].players[player.id_] = player

    def remove(self, player_id: UUID) -> None:
        player = self._player_map.pop(player_id)
        self._room_map[player.room.id_].players.pop(player_id)

    def does_room_exist(self, room_id: int) -> bool:
        return room_id in self._room_map

    def create_room(self, room: m.Room) -> None:
        if self.does_room_exist(room.id_):
            raise ValueError('Room already exists')
        self._room_map[room.id_] = room
