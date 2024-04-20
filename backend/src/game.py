import random
from datetime import datetime
from typing import Any, cast

import httpx

import src.models as d
import src.schemas as s
from config import get_config


def check_word(word: str) -> s.Word:
    client = httpx.Client()
    response = client.get(f'{get_config().DICTIONARY_API_URL}{word}')

    # TODO: Handle connection errors and other exceptions
    if response.status_code == 404:
        # TODO: Function does 2  things - unpacks response and returns False on failed validation
        return s.Word(content=word, is_correct=False)

    definitions = {
        meaning['partOfSpeech']: meaning['definitions'][0]['definition']
        for meaning in response.json()[0]['meanings']
    }
    return s.Word(content=word, is_correct=True, description=definitions)


class OrderedPlayers(list):
    """Augmented list class which mimics circular singly-linked list. Randomizes the order of players upon instantiation and keeps track of the current player."""

    def __init__(self, players: list[s.GamePlayer]) -> None:
        super().__init__(players)
        random.shuffle(self)

        self._current_idx = -1 if len(self) == 0 else 0

    @property
    def current_idx(self) -> int:
        return self._current_idx

    @current_idx.setter
    def current_idx(self, value: Any) -> None:
        raise AttributeError('`current` attr can only be read')

    @property
    def current(self) -> s.GamePlayer:
        return self[self._current_idx]

    def next(self) -> None:
        """Iterate to the next player in the circular manner."""
        if len(self) == 0:
            raise ValueError('Next player cannot be iterated to in an empty list')
        self._current_idx = (self._current_idx + 1) % len(self)

    def remove_current(self) -> s.GamePlayer:
        """Remove current player from the list, and move to the previous player."""
        player = self.pop(self._current_idx)

        if len(self) != 0:
            self._current_idx = (self._current_idx - 1) % len(self)
        else:
            self._current_idx = -1

        return player


# TODO: Build and use abstract interface when you figure out the interface
# class Game(Protocol):
#     id_: int
#     status: d.GameStatusEnum
#     turns: list[s.Turn]

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
        self.status = d.GameStatusEnum.STARTING
        self.rules = rules

        game_players = [
            s.GamePlayer(score=self.rules.start_score, mistakes=0, **player.to_dict())
            for player in players
        ]
        self.players = OrderedPlayers(game_players)
        self.lost_players: list[s.GamePlayer] = []

        self._turns: list[s.Turn] = []
        self._current_turn: s.Turn | None = None

        self.words: set[s.Word] = set()
        self.events: list[s.GameEvent] = []  # Must be emptied after each turn

    @property
    def turns(self) -> list[s.Turn]:
        return self._turns

    @turns.setter
    def turns(self, value: Any) -> None:
        raise AttributeError('`turns` attr can only be read')

    @property
    def current_turn(self) -> s.Turn | None:
        return self._current_turn

    @current_turn.setter
    def current_turn(self, value: Any) -> None:
        raise AttributeError('`current_turn` attr can only be read')

    @property
    def time_left_in_turn(self) -> float:
        current_turn = cast(s.Turn, self.current_turn)
        time_elapsed = datetime.utcnow() - current_turn.started_on
        return self.rules.round_time - time_elapsed.total_seconds()

    def start_turn(self) -> s.StartTurnState:
        if self.status == d.GameStatusEnum.FINISHED:
            raise ValueError('Game is already finished')
        self.status = d.GameStatusEnum.IN_PROGRESS
        self.events = []

        if self._turns:  # Don't iterate on the first turn
            self.players.next()
        self._current_turn = s.Turn(
            started_on=datetime.utcnow(), player_id=self.players.current.id_
        )

        return s.StartTurnState(
            current_turn=s.TurnOut(
                player_idx=self.players.current_idx, **self.current_turn.model_dump()
            ),
            status=self.status,
        )  # type: ignore

    def process_turn(self, word: str | None = None) -> s.EndTurnState:
        current_turn = cast(s.Turn, self.current_turn)
        current_turn.ended_on = datetime.utcnow()
        time_elapsed = current_turn.ended_on - current_turn.started_on

        # `word` arg should not be passed when the turn has timed out
        assert not word and time_elapsed.total_seconds() > self.rules.round_time  # noqa: PT018
        if not word:
            current_turn.word = None
            current_turn.info = 'Turn time exceeded'
        else:
            current_turn.word, current_turn.info = self._validate_word(word)

        self._evaluate_turn()
        self._evaluate_game()
        self._turns.append(current_turn)

        return s.EndTurnState(
            type_='end_turn',
            players=self.players,
            lost_players=self.lost_players,
            current_turn=s.TurnOut(
                player_idx=self.players.current_idx,
                **self.current_turn.model_dump(),
            ),
        )

    def did_turn_timed_out(self, turn_no: int) -> bool:
        """Check if the turn in the game has timed out."""
        if turn_no <= len(self.turns):
            return False
        return True

    def _validate_word(self, word: str) -> tuple[s.Word, str]:
        word = word.lower()
        last_word = (
            self._turns[-1].word.content if self.turns else None
        )  # Ignore on the first turn
        if last_word and not word.startswith(last_word[-1]):
            return (
                s.Word(content=word, is_correct=False),
                'Word does not start with the last letter of the previous word',
            )

        if word in self.words:
            return s.Word(content=word, is_correct=False), 'Word has already been used'

        word_obj = check_word(word)
        if not word_obj.is_correct:
            return word_obj, 'Word does not exist'

        self.words.add(word_obj)
        return word_obj, 'Word is correct'

    def _evaluate_turn(self) -> None:
        current_turn = cast(s.Turn, self._current_turn)

        # TODO: Deal with edge cases like penalty == 0 . Maybe figure out a better way to handle this
        did_turn_timed_out = not current_turn.word
        if did_turn_timed_out or not current_turn.word.is_correct:
            self.players.current.mistakes += 1
            self.players.current.score += self.rules.penalty
        else:
            self.players.current.score += self.rules.reward

        # Player lost
        if self.players.current.score <= 0:
            lost_player = self.players.remove_current()
            self.lost_players.append(lost_player)
            self.events.append(s.PlayerLostEvent(player_name=lost_player.name))

    def _evaluate_game(self) -> None:
        # Handle case with more than 1 player playing
        if len(self.players) == 1 and len(self.lost_players) > 0:
            self.status = d.GameStatusEnum.FINISHED
            self.events.append(s.GameFinishedEvent())

        # Handle case with only 1 player playing
        if len(self.players) == 0 and len(self.lost_players) > 0:
            self.status = d.GameStatusEnum.FINISHED
            self.events.append(s.GameFinishedEvent())


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
