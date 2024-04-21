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
    currentTurn: undefined,
    setGameCurrentTurn: () => {},
    gameTurns: undefined,
    setGameTurns: () => {},
    updateGameState: (newGameState: GameState) => {},
    resetGameState: () => {},
};

export default function GameStoreSlice(switchMode: (mode: "lobby" | "room" | "game") => void) {
    const [gameId, setGameId] = useState<number | undefined>(undefined);
    const [gameStatus, setGameStatus] = useState<
        "Starting" | "In progress" | "Finished" | undefined
    >(undefined);
    const [gameRules, setGameRules] = useState<DeathmatchRules | undefined>(undefined);

    const [gamePlayers, setGamePlayers] = useState<GamePlayer[] | undefined>(undefined);
    const [gameLostPlayers, setGameLostPlayers] = useState<GamePlayer[] | undefined>(undefined);

    const [currentTurn, setGameCurrentTurn] = useState<Turn | null | undefined>(undefined);
    const [gameTurns, setGameTurns] = useState<Turn[] | undefined>(undefined);

    function updateGameState(newGameState: GameState) {
        switch (newGameState.type) {
            case "start_game":
                switchMode("game");

                setGameId(newGameState.id);
                setGameStatus(newGameState.status);
                setGameRules(newGameState.rules);
                setGamePlayers(newGameState.players);
                setGameLostPlayers(newGameState.lost_players);

                // Also initialize FE-only state
                setGameTurns([]);
                break;
            case "end_game":
                setGameStatus("Finished");

                switchMode("room");
                break;
            case "start_turn":
                newGameState.status && setGameStatus(newGameState.status);
                setGameCurrentTurn(newGameState.current_turn);
                break;
            case "end_turn":
                setGamePlayers(newGameState.players);
                setGameLostPlayers(newGameState.lost_players);
                setGameTurns((prevGameTurns) => [
                    ...(prevGameTurns || []),
                    newGameState.current_turn,
                ]);
                break;
        }
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
        currentTurn,
        setGameCurrentTurn,
        gameTurns,
        setGameTurns,
        updateGameState,
        resetGameState,
    };
}
