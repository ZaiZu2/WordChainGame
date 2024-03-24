import { createContext, useContext, useState, useEffect } from "react";
import { Player, ChatMessage, LobbyState, GameState, RoomState, AllTimeStatistics } from "@/types";
import apiClient from "../apiClient";
import { AuthError } from "../errors";
import { UUID } from "crypto";
import { CHAT_MESSAGE_LIMIT } from "../config";

export type StoreContext = {
    chatMessages: ChatMessage[];
    lobbyState: LobbyState | null;
    roomState: RoomState | null;
    gameState: GameState | null;
    allTimeStatistics: AllTimeStatistics | undefined;
    mode: "lobby" | "room" | "game";
    player: Player | null | undefined;
    setMode: (mode: "lobby" | "room" | "game") => void;
    updateChatMessages: (newChatMessages: ChatMessage[]) => void;
    purgeChatMessages: () => void;
    updateLobbyState: (newLobbyState: LobbyState | null) => void;
    updateRoomState: (newRoomState: RoomState | null) => void;
    updateGameState: (newGameState: GameState | null) => void;
    setAllTimeStatistics: (newAllTimeStatistics: AllTimeStatistics) => void;
    logIn: (id: UUID) => void;
    logOut: () => void;
    showCreateRoomModal: boolean;
    toggleCreateRoomModal: (show: boolean) => void;
};

const StoreContextObject = createContext<StoreContext>({
    chatMessages: [],
    lobbyState: null,
    roomState: null,
    gameState: null,
    mode: "lobby",
    player: null,
    allTimeStatistics: undefined,
    setMode: (mode: "lobby" | "room" | "game") => {},
    updateChatMessages: (newChatMessages: ChatMessage[]) => {},
    purgeChatMessages: () => {},
    updateLobbyState: (newLobbyState: LobbyState | null) => {},
    updateRoomState: (newRoomState: RoomState | null) => {},
    updateGameState: (newGameState: GameState | null) => {},
    setAllTimeStatistics: (newAllTimeStatistics: AllTimeStatistics) => {},
    logIn: () => {},
    logOut: () => {},
    showCreateRoomModal: false,
    toggleCreateRoomModal: (show: boolean) => {},
});

export function useStore() {
    return useContext(StoreContextObject);
}

export default function StoreProvider({ children }: { children: React.ReactNode }) {
    const [mode, setMode] = useState<"lobby" | "room" | "game">("lobby");
    const [player, setPlayer] = useState<Player | null | undefined>();
    const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
    const [lobbyState, setLobbyState] = useState<LobbyState | null>(null);
    const [roomState, setRoomState] = useState<RoomState | null>(null);
    const [gameState, setGameState] = useState<GameState | null>(null);
    const [allTimeStatistics, setAllTimeStatistics] = useState<AllTimeStatistics | undefined>(
        undefined
    );

    const [showCreateRoomModal, toggleCreateRoomModal] = useState(false);

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

    function purgeChatMessages() {
        setChatMessages([]);
    }

    function updateChatMessages(newChatMessages: ChatMessage[]) {
        setChatMessages((prevChatMessages) => {
            const tempMessages = [...prevChatMessages, ...newChatMessages];
            if (tempMessages.length > CHAT_MESSAGE_LIMIT) {
                return tempMessages.slice(tempMessages.length - CHAT_MESSAGE_LIMIT);
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
                    stats: newLobbyState.stats
                        ? { ...prevLobbyState.stats, ...newLobbyState.stats }
                        : prevLobbyState.stats,
                };
            }
        });
    }

    function updateRoomState(newRoomState: RoomState | null) {
        setRoomState((prevRoomState) => {
            if (
                newRoomState === null ||
                prevRoomState === null ||
                newRoomState.id !== prevRoomState.id
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
                allTimeStatistics,
                mode,
                setMode,
                player,
                updateChatMessages,
                purgeChatMessages,
                updateLobbyState,
                updateRoomState,
                updateGameState,
                setAllTimeStatistics,
                logIn,
                logOut,
                showCreateRoomModal,
                toggleCreateRoomModal,
            }}
        >
            {children}
        </StoreContextObject.Provider>
    );
}
