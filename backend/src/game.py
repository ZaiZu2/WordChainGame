import random
from datetime import datetime
from typing import cast

import httpx

import src.models as d
import src.schemas as s
from config import get_config


class IncorrectWordError(Exception):
    pass


def validate_word(word: str) -> dict:
    client = httpx.Client()
    response = client.get(f'{get_config().DICTIONARY_API_URL}{word}')

    # TODO: Handle connection errors and other exceptions
    if response.status_code == 404:
        raise IncorrectWordError()

    definitions = {
        meaning['partOfSpeech']: meaning['definitions'][0]['definition']
        for meaning in response.json()['meanings']
    }
    return definitions


class OrderedPlayers(list):
    """Augmented list class which mimics circular singly-linked list. Randomizes the order of players upon instantiation and keeps track of the current player."""

    def __init__(self, players: list[s.GamePlayer]) -> None:
        super().__init__(players)
        random.shuffle(self)

        self.current_idx = 0

    @property
    def current(self) -> s.GamePlayer:
        return self[self.current_idx]

    def next(self) -> None:
        """Iterate to the next player in the circular manner."""
        self.current_idx = (self.current_idx + 1) % len(self)

    def remove_current(self) -> s.GamePlayer:
        """Remove current player from the list."""
        player = self.pop(self.current_idx)
        self.current_idx = (self.current_idx - 1) % len(self)
        return player


# TODO: Build and use abstract interface when you figure out the interface
# class Game(Protocol):
#     id_: int
#     status: d.GameStatusEnum
#     turns: list[d.Turn]

#     def __init__(self, rules: s.Rules):
#         ...

#     def start_turn(self) -> s.TurnResults:
#         ...

#     def process_turn(self, word: str) -> s.TurnResults:
#         ...


class Deathmatch:
    def __init__(
        self, id_: int, players: list[d.Player], rules: s.DeathmatchRules
    ) -> None:
        self.id_ = id_
        self.status = d.GameStatusEnum.IN_PROGRESS
        self.rules = rules

        game_players = [
            s.GamePlayer(score=self.rules.start_score, mistakes=0, **player.to_dict())
            for player in players
        ]
        self.players = OrderedPlayers(game_players)
        self.lost_players: list[s.GamePlayer] = []

        self.turns: list[d.Turn] = []
        self.current_turn: d.Turn | None = None

    def start_turn(self) -> None:
        if self.status == d.GameStatusEnum.FINISHED:
            raise ValueError('Game is already finished')

        if self.turns:  # Don't iterate on the first turn
            self.players.next()
        self.current_turn = d.Turn(
            started_on=datetime.utcnow(), player_id=self.players.current
        )

    def process_turn(self, word: str) -> list[s.PlayerLostEvent | s.GameFinishedEvent]:
        current_turn = cast(d.Turn, self.current_turn)
        current_turn.ended_on = datetime.utcnow()
        time_elapsed = current_turn.ended_on - current_turn.started_on

        if time_elapsed.total_seconds() > self.rules.round_time:
            current_turn.word = None
            current_turn.is_correct = False
        elif validate_word(word):
            current_turn.word = word
            current_turn.is_correct = True
        else:
            current_turn.word = word
            current_turn.is_correct = False

        turn_event = self._evaluate_turn()
        game_event = self._evaluate_game()

        self.turns.append(current_turn)
        self.current_turn = None
        return [*turn_event, *game_event]

    # def _finalize_turn(self) -> s.TurnResults:
    #     current_turn = cast(d.Turn, self.current_turn)
    #     self.turns.append(current_turn)
    #     self.current_turn = None
    #     return s.TurnResults(turn=current_turn)

    def _evaluate_turn(self) -> list[s.PlayerLostEvent]:
        current_turn = cast(d.Turn, self.current_turn)

        # TODO: Deal with edge cases like penalty == 0 . Maybe figure out a better way to handle this
        if not current_turn.word or not current_turn.is_correct:
            self.players.current.mistakes += 1
            self.players.current.score -= self.rules.penalty
        else:
            self.players.current.score += self.rules.reward

        # Player lost
        if self.players.current.score <= 0:
            lost_player = self.players.remove_current()
            self.lost_players.append(lost_player)
            return [s.PlayerLostEvent(player_name=lost_player.name)]
        return []

    def _evaluate_game(self) -> list[s.GameFinishedEvent]:
        if len(self.players) == 1:
            self.status = d.GameStatusEnum.FINISHED
            return [s.GameFinishedEvent()]
        return []


class GameManager:
    """
    Manages active games, storing them in memory. Upon game finalization, the game is
    removed from the manager and returned to be persisted in DB.
    """

    def __init__(self) -> None:
        self.games: dict[int, Deathmatch] = {}

    def get(self, game_id: int) -> Deathmatch:
        return self.games[game_id]

    def create(self, game_db: d.Game) -> Deathmatch:
        if game_db.rules['type_'] == s.GameTypeEnum.DEATHMATCH:
            rules = s.DeathmatchRules(**game_db.rules)
            game = self.games[game_db.id_] = Deathmatch(
                game_db.id_, game_db.players, rules
            )
            return game
        else:
            raise NotImplementedError('Unsupported game type')

    def end(self, game_id: int) -> Deathmatch:
        game = self.games[game_id]
        game.status = d.GameStatusEnum.FINISHED
        del self.games[game_id]
        return game
