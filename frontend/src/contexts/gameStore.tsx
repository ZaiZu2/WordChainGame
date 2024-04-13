import { useState } from "react";

import { DeathmatchRules, GamePlayer, GameState, Turn } from "@/types";

export const initialGameStoreSlice = {
    gameId: undefined,
    setGameId: () => {},
    gameStatus: undefined,
    setGameStatus: () => {},
    gameRules: undefined,
    setGameRules: () => {},
    gamePlayers: undefined,
    setGamePlayers: () => {},
    gameLostPlayers: undefined,
    setGameLostPlayers: () => {},
    gameCurrentTurn: undefined,
    setGameCurrentTurn: () => {},
    gameTurns: undefined,
    setGameTurns: () => {},
    updateGameState: (newGameState: GameState) => {},
    resetGameState: () => {},
};

export default function GameStoreSlice() {
    const [gameId, setGameId] = useState<number | undefined>(undefined);
    const [gameStatus, setGameStatus] = useState<"In progress" | "Finished" | undefined>(undefined);
    const [gameRules, setGameRules] = useState<DeathmatchRules | undefined>(undefined);

    const [gamePlayers, setGamePlayers] = useState<GamePlayer[] | undefined>(undefined);
    const [gameLostPlayers, setGameLostPlayers] = useState<GamePlayer[] | undefined>(undefined);

    const [gameCurrentTurn, setGameCurrentTurn] = useState<Turn | undefined>(undefined);
    const [gameTurns, setGameTurns] = useState<Turn[] | undefined>(undefined);

    function updateGameState(newGameState: GameState) {
        setGameId(newGameState.id);
        setGameStatus(newGameState.status);
        setGameRules(newGameState.rules);
        setGamePlayers(newGameState.players);
        setGameLostPlayers(newGameState.lost_players);
        setGameCurrentTurn(newGameState.current_turn);
        setGameTurns(newGameState.turns);
    }

    function resetGameState() {
        setGameId(undefined);
        setGameStatus(undefined);
        setGameRules(undefined);
        setGamePlayers(undefined);
        setGameLostPlayers(undefined);
        setGameCurrentTurn(undefined);
        setGameTurns(undefined);
    }

    return {
        gameId,
        setGameId,
        gameStatus,
        setGameStatus,
        gamePlayers,
        setGamePlayers,
        gameLostPlayers,
        setGameLostPlayers,
        gameRules,
        setGameRules,
        gameCurrentTurn,
        setGameCurrentTurn,
        gameTurns,
        setGameTurns,
        updateGameState,
        resetGameState,
    };
}
