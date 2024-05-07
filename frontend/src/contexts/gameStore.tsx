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
    currentTurn: undefined,
    setGameCurrentTurn: () => {},
    gameTurns: undefined,
    setGameTurns: () => {},
    updateGameState: (newGameState: GameState) => {},
    resetGameState: () => {},
    gameState: undefined,
};

export default function GameStoreSlice(switchMode: (mode: "lobby" | "room" | "game") => void) {
    const [gameState, setGameState] = useState<
        "STARTED" | "ENDED" | "WAITING" | "STARTED_TURN" | "ENDED_TURN" | undefined
    >(undefined);
    const [gameId, setGameId] = useState<number | undefined>(undefined);
    const [gameStatus, setGameStatus] = useState<
        "Starting" | "In progress" | "Finished" | undefined
    >(undefined);
    const [gameRules, setGameRules] = useState<DeathmatchRules | undefined>(undefined);

    const [gamePlayers, setGamePlayers] = useState<GamePlayer[] | undefined>(undefined);

    const [currentTurn, setGameCurrentTurn] = useState<Turn | null | undefined>(undefined);
    const [gameTurns, setGameTurns] = useState<Turn[] | undefined>(undefined);

    function updateGameState(newGameState: GameState) {
        setGameState(newGameState.state);

        switch (newGameState.state) {
            case "STARTED":
                resetGameState();
                switchMode("game");

                setGameId(newGameState.id);
                setGameStatus(newGameState.status);
                setGameRules(newGameState.rules);
                setGamePlayers(newGameState.players);

                // Also initialize FE-only state
                setGameTurns([]);
                break;
            case "ENDED":
                setGameStatus("Finished");
                break;
            case "WAITING":
                setGameState(newGameState.state);
                break;
            case "STARTED_TURN":
                newGameState.status && setGameStatus(newGameState.status);
                setGameCurrentTurn(newGameState.current_turn);
                break;
            case "ENDED_TURN":
                setGamePlayers(newGameState.players);
                setGameTurns((prevGameTurns) => [
                    ...(prevGameTurns || []),
                    newGameState.current_turn,
                ]);
                break;
            default:
                console.log("Unknown game state", newGameState);
        }
    }

    function resetGameState() {
        setGameId(undefined);
        setGameStatus(undefined);
        setGameRules(undefined);
        setGamePlayers(undefined);
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
        gameRules,
        setGameRules,
        currentTurn,
        setGameCurrentTurn,
        gameTurns,
        setGameTurns,
        updateGameState,
        resetGameState,
        gameState,
    };
}
