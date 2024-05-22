import random
from datetime import datetime
from typing import Any, Iterable, cast

import src.schemas.domain as d
import src.schemas.validation as v
from config import get_config
from src.game.utils import check_word_correctness


class OrderedPlayers(list):
    """Augmented list class which mimics circular singly-linked list. Randomizes the order of players upon instantiation and keeps track of the current player."""

    def __init__(self, players: list[d.GamePlayer]) -> None:
        super().__init__(players)
        random.shuffle(self)

        self._current_idx = -1 if len(self) == 0 else 0
        self.current_place = len(
            self
        )  # Place for which players are currently competing

    @property
    def current_idx(self) -> int:
        return self._current_idx

    @current_idx.setter
    def current_idx(self, value: Any) -> None:
        raise AttributeError('`current` attr can only be read')

    @property
    def current(self) -> d.GamePlayer:
        return self[self._current_idx]

    def next(self) -> None:
        """Iterate to the next player in the circular manner."""
        if len(self) == 0:
            raise ValueError('Next player cannot be iterated to for an empty list')

        start_idx = self._current_idx
        while True:
            # TODO: This is just wrong, figure out a better way
            # 1. Might fall into infinite loop
            # Ugly, weird, needs to handle 1 player / multiplayer game separately
            self._current_idx = (self._current_idx + 1) % len(self)

            if len(self) != 1 and self._current_idx == start_idx:
                raise ValueError('All but one player are out of the game')
            if self.current.in_game:
                break
            if all(not player.in_game for player in self):
                raise ValueError('All players are out of the game')

    def remove_current(self) -> None:
        """Remove current player from the game and set his final ranking."""
        self.current.in_game = False
        self.current.place = self.current_place
        self.current_place -= 1


class Deathmatch:
    def __init__(
        self,
        id_: int,
        room_id: int,
        players: Iterable[d.Player],
        rules: d.DeathmatchRules,
    ) -> None:
        self.id_ = id_
        self.room_id = room_id
        self.rules = rules
        self.state: d.GameStateEnum = d.GameStateEnum.CREATING

        game_players = [
            d.GamePlayer(id_=player.id_, name=player.name, score=self.rules.start_score)
            for player in players
        ]
        self.players = OrderedPlayers(game_players)

        self._turns: list[d.Turn] = []
        self._current_turn: d.Turn | None = None

        self.words: set[str] = set()  # Quick lookup for used words
        self.events: list[d.GameEvent] = []  # Must be emptied after each turn

    @property
    def turns(self) -> list[d.Turn]:
        return self._turns

    @turns.setter
    def turns(self, value: Any) -> None:
        raise AttributeError('`turns` attr can only be read')

    @property
    def current_turn(self) -> d.Turn | None:
        return self._current_turn

    @current_turn.setter
    def current_turn(self, value: Any) -> None:
        raise AttributeError('`current_turn` attr can only be read')

    @property
    def time_left_in_turn(self) -> float:
        current_turn = cast(d.Turn, self.current_turn)
        time_elapsed = datetime.utcnow() - current_turn.started_on
        return self.rules.round_time - time_elapsed.total_seconds()

    def start(self) -> v.StartGameState:
        if self.state != d.GameStateEnum.CREATING:
            raise ValueError(f'Game cannot be started in the {self.state} game state')
        self.state = d.GameStateEnum.STARTED

        return v.StartGameState(
            id_=self.id_,
            players=self.players,
            rules=self.rules,  # type: ignore
        )

    def wait(self) -> v.WaitState:
        self.state = d.GameStateEnum.WAITING
        return v.WaitState()

    def start_turn(self) -> v.StartTurnState:
        if self.state not in [d.GameStateEnum.CREATING, d.GameStateEnum.WAITING]:
            raise ValueError(f'Turn cannot be started in the {self.state} game state')
        self.state = d.GameStateEnum.STARTED_TURN
        self.events.clear()

        if self.turns:  # Don't iterate on the first turn
            self.players.next()

        current_turn = d.Turn(
            started_on=datetime.utcnow(), player_id=self.players.current.id_
        )
        self._current_turn = current_turn

        return v.StartTurnState(
            current_turn=v.TurnOut(
                player_idx=self.players.current_idx, **current_turn.to_dict()
            ),
        )

    def end_turn_in_time(self, word: str) -> v.EndTurnState:
        if self.state != d.GameStateEnum.STARTED_TURN:
            raise ValueError(f'Turn cannot be ended in the {self.state} game state')
        self.state = d.GameStateEnum.ENDED_TURN

        current_turn = cast(d.Turn, self.current_turn)
        current_turn.ended_on = datetime.utcnow()
        current_turn.word, current_turn.info = self._validate_word(word)

        self._evaluate_turn()
        self._turns.append(current_turn)

        return v.EndTurnState(
            players=self.players,
            current_turn=v.TurnOut(
                player_idx=self.players.current_idx,
                **current_turn.to_dict(),
            ),
        )

    def end_turn_timed_out(self) -> v.EndTurnState:
        if self.state != d.GameStateEnum.STARTED_TURN:
            raise ValueError(f'Turn cannot be ended in the {self.state} game state')
        self.state = d.GameStateEnum.ENDED_TURN

        current_turn = cast(d.Turn, self.current_turn)
        current_turn.ended_on = datetime.utcnow()
        current_turn.word = None
        current_turn.info = 'Turn time exceeded'

        time_elapsed = current_turn.ended_on - current_turn.started_on
        assert (
            time_elapsed.total_seconds()
            < self.rules.round_time + get_config().MAX_TURN_TIME_DEVIATION
        )

        self._evaluate_turn()
        self.turns.append(current_turn)

        return v.EndTurnState(
            players=self.players,
            current_turn=v.TurnOut(
                player_idx=self.players.current_idx,
                **current_turn.to_dict(),
            ),
        )

    def end(self) -> v.EndGameState:
        if self.state != d.GameStateEnum.ENDED_TURN:
            raise ValueError(f'Game cannot be ended in the {self.state} game state')

        self.events.clear()  # Clear events from the previous turn
        if len(self.players) == 1:
            self.events.append(d.GameFinishedEvent(chain_length=len(self.words)))
        else:
            winner: d.GamePlayer = next(
                game_player for game_player in self.players if game_player.in_game
            )
            self.events.append(d.PlayerWonEvent(player_name=winner.name))
            self.events.append(d.GameFinishedEvent(chain_length=len(self.words)))
        return v.EndGameState()

    def is_finished(self) -> bool:
        # Handle case with just 1 player playing
        if len(self.players) == 1 and not self.players.current.in_game:
            return True

        # Handle case with more than 1 player playing
        players_in_game = len([player for player in self.players if player.in_game])
        if len(self.players) > 1 and players_in_game == 1:
            return True

        return False

    def _validate_word(self, word: str) -> tuple[d.Word, str]:
        word = word.lower()
        if not self._is_compatible_with_previous_word(word):
            return (
                d.Word(content=word, is_correct=False),
                'Word does not start with the last letter of the previous word',
            )

        word_obj = check_word_correctness(word)
        if not word_obj.is_correct:
            return word_obj, 'Word does not exist'

        if word in self.words:
            return d.Word(content=word, is_correct=False), 'Word has already been used'

        self.words.add(word)
        return word_obj, 'Word is correct'

    def _is_compatible_with_previous_word(self, word: str) -> bool:
        """Check if the word is valid with the previous word (it starts with the last letter of the previous word)."""
        if len(self.turns) == 0:
            return True

        # Find the last turn in which the word was passed
        for i in range(len(self.turns) - 1, -1, -1):
            turn = self.turns[i]
            if not turn.word:
                continue

            previous_word = turn.word.content
            if word.startswith(previous_word[-1]):
                return True
            break

        return False

    def _evaluate_turn(self) -> None:
        current_turn = cast(d.Turn, self._current_turn)

        # TODO: Deal with edge cases like penalty == 0 . Maybe figure out a better way
        # to handle this

        # If player didn't pass a word or the word is incorrect, give him a penalty
        if not current_turn.word or not current_turn.word.is_correct:
            self.players.current.mistakes += 1
            self.players.current.score += self.rules.penalty
        else:
            self.players.current.score += self.rules.reward

        # Player lost
        if self.players.current.score <= 0:
            self.players.remove_current()

            if len(self.players) != 1:
                self.events.append(
                    d.PlayerLostEvent(player_name=self.players.current.name)
                )
