import useWebSocket from "react-use-websocket";
import React, { createContext, useContext, useState, useEffect } from "react";
import {
    WebSocketMessage,
    ChatMessage,
    LobbyState,
    GameState,
    ConnectionState,
    Room,
    RoomState,
} from "@/types";
import { WEBSOCKET_URL } from "../config";
import { usePlayer } from "../contexts/PlayerContext";
import { CHAT_MESSAGE_LIMIT } from "../config";

export type WebSocketContext = {
    sendChatMessage: (message: string, room_id: number) => void;
    chatMessages: ChatMessage[];
    lobbyState: LobbyState | null;
    roomState: RoomState | null;
    gameState: GameState | null;
};

export const WebSocketContextObject = createContext<WebSocketContext>({
    sendChatMessage: (message: string, room_id: number) => {},
    chatMessages: [],
    lobbyState: null,
    roomState: null,
    gameState: null,
});

export function useWebSocketContext(): WebSocketContext {
    return useContext(WebSocketContextObject);
}

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
    const { logOut, player } = usePlayer();
    const { sendJsonMessage, lastJsonMessage } = useWebSocket(WEBSOCKET_URL, {});

    const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
    const [lobbyState, setLobbyState] = useState<LobbyState | null>(null);
    const [roomState, setRoomState] = useState<RoomState | null>(null);
    const [gameState, setGameState] = useState<GameState | null>(null);

    useEffect(
        function parseMessage() {
            if (lastJsonMessage === null) return;

            const websocketMessage = JSON.parse(lastJsonMessage as string) as WebSocketMessage;
            switch (websocketMessage.type) {
                case "chat":
                    setChatMessages((prevChatMessages) => {
                        const tempMessages = [
                            ...prevChatMessages,
                            websocketMessage.payload as ChatMessage,
                        ];
                        if (tempMessages.length > CHAT_MESSAGE_LIMIT) {
                            tempMessages.shift();
                        }
                        return tempMessages;
                    });
                    console.log("chat", websocketMessage.payload);
                    break;

                case "lobby_state":
                    setLobbyState((prevLobbyState) => {
                        const newLobbyState = websocketMessage.payload as LobbyState;
                        if (prevLobbyState === null) {
                            return newLobbyState;
                        } else {
                            return {
                                ...prevLobbyState,
                                ...newLobbyState,
                                rooms: newLobbyState.rooms
                                    ? runDifferentialUpdate(
                                          prevLobbyState.rooms,
                                          newLobbyState.rooms,
                                      )
                                    : prevLobbyState.rooms,
                                players: newLobbyState.players
                                    ? runDifferentialUpdate(
                                          prevLobbyState.players,
                                          newLobbyState.players,
                                      )
                                    : prevLobbyState.players,
                            };
                        }
                    });
                    console.log("lobby", websocketMessage.payload);
                    break;

                case "room_state":
                    setRoomState((prevRoomState) => {
                        const newRoomState = websocketMessage.payload as RoomState;
                        if (
                            prevRoomState === null ||
                            prevRoomState.room_id !== newRoomState.room_id
                        ) {
                            return newRoomState;
                        } else {
                            return {
                                ...prevRoomState,
                                ...newRoomState,
                                players: newRoomState.players
                                    ? runDifferentialUpdate(
                                          prevRoomState.players,
                                          newRoomState.players,
                                      )
                                    : prevRoomState.players,
                            };
                        }
                    });
                    console.log("room", websocketMessage.payload);
                    break;

                case "game_state":
                    setGameState(websocketMessage.payload as GameState);
                    break;

                case "connection_state":
                    const connState = websocketMessage.payload as ConnectionState;
                    if (connState.code === 4001) {
                        // TODO: Show toast saying that the player can only use one client at a time
                        logOut();
                    }
                    console.log("connection", websocketMessage.payload);
                    break;
            }
        },
        [lastJsonMessage, logOut],
    );

    function sendChatMessage(message: string, room_id: number) {
        const websocketMessage = {
            type: "chat",
            payload: {
                player_name: player?.name,
                room_id: room_id,
                content: message,
            },
        } as WebSocketMessage;
        sendJsonMessage(websocketMessage);
    }

    function runDifferentialUpdate<T>(
        prevObj: Record<string, T>,
        newObj: Record<string, T>,
    ): Record<string, T> {
        const merged = { ...prevObj };
        for (const [id, obj] of Object.entries(newObj)) {
            if (obj === null) {
                delete merged[id];
            }
            merged[id] = obj;
        }
        return merged;
    }

    return (
        <WebSocketContextObject.Provider
            value={{ sendChatMessage, chatMessages, lobbyState, roomState, gameState }}
        >
            {children}
        </WebSocketContextObject.Provider>
    );
}
