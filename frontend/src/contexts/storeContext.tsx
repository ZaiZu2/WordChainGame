import { createContext, useContext, useState, useEffect } from "react";
import { Player, ChatMessage, LobbyState, GameState, RoomState } from "@/types";
import apiClient from "../apiClient";
import { AuthError } from "../errors";
import { UUID } from "crypto";
import { CHAT_MESSAGE_LIMIT } from "../config";

export type StoreContext = {
    chatMessages: ChatMessage[];
    lobbyState: LobbyState | null;
    roomState: RoomState | null;
    gameState: GameState | null;
    player: Player | null | undefined;
    updateChatMessages: (newChatMessage: ChatMessage) => void;
    updateLobbyState: (newLobbyState: LobbyState | null) => void;
    updateRoomState: (newRoomState: RoomState | null) => void;
    updateGameState: (newGameState: GameState | null) => void;
    logIn: (id: UUID) => void;
    logOut: () => void;
};

const StoreContextObject = createContext<StoreContext>({
    chatMessages: [],
    lobbyState: null,
    roomState: null,
    gameState: null,
    player: null,
    updateChatMessages: (newChatMessage: ChatMessage) => {},
    updateLobbyState: (newLobbyState: LobbyState | null) => {},
    updateRoomState: (newRoomState: RoomState | null) => {},
    updateGameState: (newGameState: GameState | null) => {},
    logIn: () => {},
    logOut: () => {},
});

export function useStore() {
    return useContext(StoreContextObject);
}

export default function StoreProvider({ children }: { children: React.ReactNode }) {
    const [player, setPlayer] = useState<Player | null | undefined>();
    const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
    const [lobbyState, setLobbyState] = useState<LobbyState | null>(null);
    const [roomState, setRoomState] = useState<RoomState | null>(null);
    const [gameState, setGameState] = useState<GameState | null>(null);

    useEffect(function checkPlayerSessionCookie() {
        // If HTTP-only cookie is set and still valid, the player will get immediately
        // logged in
        (async () => {
            try {
                const response = await apiClient.get<Player>("/players/me");
                setPlayer(response.body);
            } catch (error) {
                if (error instanceof AuthError) {
                    setPlayer(null);
                }
            }
        })();
    }, []);

    async function logIn(id: UUID) {
        const body = id === undefined ? { id: player?.id } : { id: id };
        const response = await apiClient.post<Player>("/players/login", { body: body });
        setPlayer(response.body);
    }

    async function logOut() {
        await apiClient.post<null>("/players/logout", { body: { id: player?.id } });
        setPlayer(null);
    }

    function updateChatMessages(newChatMessage: ChatMessage) {
        setChatMessages((prevChatMessages) => {
            const tempMessages = [...prevChatMessages, newChatMessage];
            if (tempMessages.length > CHAT_MESSAGE_LIMIT) {
                tempMessages.shift();
            }
            return tempMessages;
        });
    }

    function updateLobbyState(newLobbyState: LobbyState | null) {
        setLobbyState((prevLobbyState) => {
            if (newLobbyState === null || prevLobbyState === null) {
                return newLobbyState;
            } else {
                return {
                    ...prevLobbyState,
                    ...newLobbyState,
                    rooms: newLobbyState.rooms
                        ? runDifferentialUpdate(prevLobbyState.rooms, newLobbyState.rooms)
                        : prevLobbyState.rooms,
                    players: newLobbyState.players
                        ? runDifferentialUpdate(prevLobbyState.players, newLobbyState.players)
                        : prevLobbyState.players,
                };
            }
        });
    }

    function updateRoomState(newRoomState: RoomState | null) {
        setRoomState((prevRoomState) => {
            if (
                newRoomState === null ||
                prevRoomState === null ||
                newRoomState.room_id !== prevRoomState.room_id
            ) {
                return newRoomState;
            } else {
                return {
                    ...prevRoomState,
                    ...newRoomState,
                    players: newRoomState.players
                        ? runDifferentialUpdate(prevRoomState.players, newRoomState.players)
                        : prevRoomState.players,
                };
            }
        });
    }

    function updateGameState(newGameState: GameState | null) {
        setGameState((prevGameState) => {
            if (newGameState === null || prevGameState === null) {
                return newGameState;
            } else {
                return { ...prevGameState, ...newGameState };
            }
        });
    }

    function runDifferentialUpdate<T extends Record<string, unknown>>(prevObj: T, newObj: T): T {
        const merged = { ...prevObj, ...newObj };
        for (const [id, obj] of Object.entries(newObj)) {
            if (obj === null) {
                delete merged[id];
            }
        }
        return merged;
    }

    return (
        <StoreContextObject.Provider
            value={{
                chatMessages,
                lobbyState,
                roomState,
                gameState,
                player,
                updateChatMessages,
                updateLobbyState,
                updateRoomState,
                updateGameState,
                logIn,
                logOut,
            }}
        >
            {children}
        </StoreContextObject.Provider>
    );
}
