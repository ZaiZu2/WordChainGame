import React, { createContext, useContext, useEffect } from "react";
import useWebSocket from "react-use-websocket";

import {
    ChatMessage,
    ConnectionState,
    GameState,
    LobbyState,
    RoomState,
    WebSocketMessage,
    WordInput,
} from "@/types";

import { WEBSOCKET_URL } from "../config";
import { useStore } from "./storeContext";

export type WebSocketContext = {
    sendChatMessage: (message: string) => void;
    sendWordInput: (word: string) => void;
};

export const WebSocketContextObject = createContext<WebSocketContext>({
    sendChatMessage: (message: string) => {},
    sendWordInput: (word: string) => {},
});

export function useWebSocketContext(): WebSocketContext {
    return useContext(WebSocketContextObject);
}

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
    const {
        player,
        roomState,
        logOut,
        updateChatMessages,
        updateLobbyState,
        updateRoomState,
        updateGameState,
        mode,
        gameId: _gameId,
    } = useStore();
    const gameId = _gameId as number;
    const { sendJsonMessage, lastJsonMessage } = useWebSocket(WEBSOCKET_URL, {});

    useEffect(
        function parseMessage() {
            if (lastJsonMessage === null) return;

            const websocketMessage = JSON.parse(lastJsonMessage as string) as WebSocketMessage;
            switch (websocketMessage.type) {
                case "chat":
                    updateChatMessages([websocketMessage.payload as ChatMessage]);
                    console.log("chat", websocketMessage.payload);
                    break;
                case "lobby_state":
                    updateLobbyState(websocketMessage.payload as LobbyState);
                    console.log("lobby", websocketMessage.payload);
                    break;
                case "room_state":
                    updateRoomState(websocketMessage.payload as RoomState);
                    console.log("room", websocketMessage.payload);
                    break;
                case "game_state":
                    updateGameState(websocketMessage.payload as GameState);
                    console.log("game", websocketMessage.payload);
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
        [lastJsonMessage]
    );

    function sendChatMessage(message: string) {
        const websocketMessage = {
            type: "chat",
            payload: {
                player_name: player?.name,
                room_id: mode === "lobby" ? 1 : (roomState?.id as number), // TODO: lobby id should be provided by the server
                content: message,
            },
        } as WebSocketMessage;
        sendJsonMessage(websocketMessage);
    }

    function sendWordInput(word: string) {
        const websocketMessage = {
            type: "game_input",
            payload: {
                type: "word_input",
                game_id: gameId,
                word: word,
            } as WordInput,
        } as WebSocketMessage;
        sendJsonMessage(websocketMessage);
        console.log("word input", websocketMessage);
    }

    return (
        <WebSocketContextObject.Provider value={{ sendChatMessage, sendWordInput }}>
            {children}
        </WebSocketContextObject.Provider>
    );
}
