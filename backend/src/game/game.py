from typing import Iterable

import src.schemas.domain as d
from src.game.deathmatch import Deathmatch


class GameManager:
    """
    Manages active games, storing them in memory. Upon game finalization, the game is
    removed from the manager and returned to be persisted in DB.
    """

    def __init__(self) -> None:
        self.games: dict[int, Deathmatch] = {}

    def get(self, game_id: int) -> Deathmatch:
        return self.games[game_id]

    def create(
        self, game_id: int, rules: d.DeathmatchRules, players: Iterable[d.Player]
    ) -> Deathmatch:
        if rules.type_ == d.GameTypeEnum.DEATHMATCH:
            game = self.games[game_id] = Deathmatch(game_id, players, rules)
            return game
        else:
            raise NotImplementedError('Unsupported game type')

    def end(self, game_id: int) -> Deathmatch:
        game = self.games[game_id]
        del self.games[game_id]
        return game


# TODO: Build and use abstract interface when you figure out the interface
# class Game(Protocol):
#     id_: int
#     status: db.GameStatusEnum
#     turns: list[s.Turn]

#     def __init__(self, rules: s.Rules):
#         ...

#     def start_turn(self) -> s.TurnResults:
#         ...

#     def process_turn(self, word: str) -> s.TurnResults:
#         ...
