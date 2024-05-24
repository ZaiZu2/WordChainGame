import { UUID } from "crypto";
import { createContext, useContext, useState } from "react";

import {
    Action as Action,
    AllTimeStatistics,
    ChatMessage,
    GameState,
    LobbyState,
    ModalConfigs,
    Player,
    RoomState,
} from "@/types";

import apiClient from "../apiClient";
import { CHAT_MESSAGE_LIMIT } from "../config";
import { AuthError } from "../errors";
import GameStoreSlice, { initialGameStoreSlice } from "./gameStore";

export type StoreContext = {
    chatMessages: ChatMessage[];
    lobbyState: LobbyState | null;
    roomState: RoomState | null;
    allTimeStatistics: AllTimeStatistics | undefined;
    mode: "lobby" | "room" | "game";
    loggedPlayer: Player | null | undefined;
    switchMode: (mode: "lobby" | "room" | "game") => void;
    updateChatMessages: (newChatMessages: ChatMessage[]) => void;
    purgeChatMessages: () => void;
    updateLobbyState: (newLobbyState: LobbyState | null) => void;
    updateRoomState: (newRoomState: RoomState | null) => void;
    updateGameState: (newGameState: GameState) => void;
    setAllTimeStatistics: (newAllTimeStatistics: AllTimeStatistics) => void;
    checkPlayerSessionCookie: () => void;
    logIn: (id: UUID) => void;
    logOut: () => void;
    executeAction: (newActionMessage: Action) => void;
    isRoomOwner: (playerName?: string) => boolean;
    isLoggedPlayersTurn: () => boolean;
    setLoggedPlayer: (player: null) => void;

    modalConfigs: ModalConfigs;
    toggleModal: <K extends keyof ModalConfigs>(
        name: K,
        config?: ModalConfigs[K],
        close?: boolean
    ) => void;
} & ReturnType<typeof GameStoreSlice>;

export const StoreContextObject = createContext<StoreContext>({
    chatMessages: [],
    lobbyState: null,
    roomState: null,
    mode: "lobby",
    loggedPlayer: null,
    allTimeStatistics: undefined,
    switchMode: (mode: "lobby" | "room" | "game") => {},
    updateChatMessages: (newChatMessages: ChatMessage[]) => {},
    purgeChatMessages: () => {},
    updateLobbyState: (newLobbyState: LobbyState | null) => {},
    updateRoomState: (newRoomState: RoomState | null) => {},
    setAllTimeStatistics: (newAllTimeStatistics: AllTimeStatistics) => {},
    checkPlayerSessionCookie: () => {},
    logIn: () => {},
    logOut: () => {},
    executeAction: (newActionMessage: Action) => {},
    isRoomOwner: (playerName?: string) => false,
    isLoggedPlayersTurn: () => true,
    setLoggedPlayer: () => {},

    modalConfigs: {},
    toggleModal: <K extends keyof ModalConfigs>(
        name: K,
        config?: ModalConfigs[K],
        close?: boolean
    ) => {},

    ...initialGameStoreSlice,
});

export function useStore() {
    return useContext(StoreContextObject);
}

export default function StoreProvider({ children }: { children: React.ReactNode }) {
    const [mode, setMode] = useState<"lobby" | "room" | "game">("lobby");
    const [loggedPlayer, setLoggedPlayer] = useState<Player | null>(null);
    const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
    const [lobbyState, setLobbyState] = useState<LobbyState | null>(null);
    const [roomState, setRoomState] = useState<RoomState | null>(null);
    const [allTimeStatistics, setAllTimeStatistics] = useState<AllTimeStatistics | undefined>(
        undefined
    );
    const gameStoreSlice = GameStoreSlice(switchMode);

    const [modalConfigs, setModalConfig] = useState<ModalConfigs>({});

    async function checkPlayerSessionCookie() {
        // If HTTP-only cookie is set and still valid, the player will get immediately
        // logged in
        (async () => {
            try {
                const response = await apiClient.get<Player>("/players/me");
                setLoggedPlayer(response.body);
            } catch (error) {
                if (error instanceof AuthError) {
                    setLoggedPlayer(null);
                }
            }
        })();
    }

    async function logIn(id: UUID) {
        const body = id === undefined ? { id: loggedPlayer?.id } : { id: id };
        const response = await apiClient.post<Player>("/players/login", { body: body });
        setLoggedPlayer(response.body);
    }

    async function logOut() {
        await apiClient.post<null>("/players/logout", { body: { id: loggedPlayer?.id } });
        setLoggedPlayer(null);
        setChatMessages([]);
        setLobbyState(null);
        setRoomState(null);
    }

    function executeAction(newActionMessage: Action) {
        switch (newActionMessage.action) {
            case "KICK_PLAYER":
                purgeChatMessages();
                switchMode("lobby");
                toggleModal("generic", {
                    title: "You have been kicked from the room",
                });
                break;
            default:
                console.log("Unknown action", newActionMessage);
        }
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
                        ? _runDifferentialUpdate(prevLobbyState.rooms, newLobbyState.rooms)
                        : prevLobbyState.rooms,
                    players: newLobbyState.players
                        ? _runDifferentialUpdate(prevLobbyState.players, newLobbyState.players)
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
                        ? _runDifferentialUpdate(prevRoomState.players, newRoomState.players)
                        : prevRoomState.players,
                };
            }
        });
    }

    function switchMode(newMode: "lobby" | "room" | "game") {
        setMode(newMode);

        if (newMode === "lobby") {
            setRoomState(null);
            gameStoreSlice.resetGameState();
        } else if (newMode === "room") {
            // setGameState(null);
        }
    }

    /**
     * Checks if the specified player is the owner of the room.
     * If no player name is provided, check if the current, logged player is the owner.
     */
    function isRoomOwner(playerName?: string): boolean {
        if (playerName === undefined) {
            return (loggedPlayer as Player).name === (roomState as RoomState).owner_name;
        } else {
            return playerName === (roomState as RoomState).owner_name;
        }
    }

    function isLoggedPlayersTurn(): boolean {
        const currentPlayerName =
            gameStoreSlice.gamePlayers?.[gameStoreSlice.currentTurn?.player_idx as number]?.name;
        return currentPlayerName === loggedPlayer?.name;
    }

    function toggleModal<K extends keyof ModalConfigs>(
        name: K,
        config?: ModalConfigs[K],
        close?: boolean
    ) {
        if (close) {
            setModalConfig((prevModalConfig) => {
                const newModalConfig = { ...prevModalConfig };
                delete newModalConfig[name];
                return newModalConfig;
            });
            return;
        }

        setModalConfig((prevModalConfig) => {
            return { ...prevModalConfig, [name]: config || {} };
        });
    }

    function _runDifferentialUpdate<T extends Record<string, unknown>>(prevObj: T, newObj: T): T {
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
                allTimeStatistics,
                mode,
                switchMode,
                loggedPlayer: loggedPlayer,
                updateChatMessages,
                purgeChatMessages,
                updateLobbyState,
                updateRoomState,
                setAllTimeStatistics,
                checkPlayerSessionCookie,
                logIn,
                logOut,
                executeAction,
                isRoomOwner,
                isLoggedPlayersTurn: isLoggedPlayersTurn,
                setLoggedPlayer,
                modalConfigs,
                toggleModal,
                ...gameStoreSlice,
            }}
        >
            {children}
        </StoreContextObject.Provider>
    );
}
