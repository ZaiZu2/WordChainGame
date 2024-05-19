from uuid import UUID

import src.schemas.domain as d


class PlayerRoomPool:
    """Manages players and rooms currently active in the game."""

    def __init__(self) -> None:
        self._room_map: dict[int, d.Room] = {d.LOBBY.id_: d.LOBBY}
        self._player_map: dict[UUID, d.Player] = {}

    @property
    def active_players(self) -> int:
        return len(self._player_map)

    @property
    def active_rooms(self) -> int:
        return len(self._room_map) - 1

    def get_player(self, player_id: UUID) -> d.Player:
        return self._player_map[player_id]

    def get_room_players(self, room_id: int) -> set[d.Player]:
        room_players = self._room_map[room_id].players
        return set(room_players.values())

    def add_player(self, player: d.Player, room_id: int) -> None:
        # TODO: Should the room be implicitly created if it doesn't exist?
        room = self.get_room(room_id=room_id)
        player.room = room
        room.players[player.id_] = player
        self._player_map[player.id_] = player

    def remove_player(self, player_id: UUID) -> None:
        player = self._player_map.pop(player_id)
        self._room_map[player.room.id_].players.pop(player_id)

    # ----------------------------------------------------------------------------------

    def get_room(
        self, *, room_id: int | None = None, player_id: UUID | None = None
    ) -> d.Room:
        """Find a room by it's ID or ID of the player who's inside it."""
        if not (bool(room_id) ^ bool(player_id)):
            raise ValueError('Either room_id or player_id must be provided')

        if room_id:
            room = self._room_map[room_id]
        elif player_id:
            player = self._player_map[player_id]
            room = player.room
        return room

    def get_rooms(self) -> set[d.Room]:
        return set(self._room_map.values()) - {d.LOBBY}

    def create_room(self, room: d.Room) -> None:
        if self.does_room_exist(room.id_):
            raise ValueError('Room already exists')
        self._room_map[room.id_] = room

    def remove_room(self, room_id: int) -> None:
        room = self.get_room(room_id=room_id)
        if room.players:
            raise ValueError('Room is not empty')

        self._room_map.pop(room_id)

    def does_room_exist(self, room_id: int) -> bool:
        return room_id in self._room_map


player_room_pool = PlayerRoomPool()
