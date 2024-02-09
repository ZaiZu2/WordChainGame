import useWebSocket from "react-use-websocket"
import React, { createContext, useContext, useState, useEffect } from 'react'
import { WebSocketContext, WebSocketMessage, ChatMessage, LobbyState, GameState } from "@/types"
import { WEBSOCKET_URL } from '../config'
import { usePlayer } from "../contexts/PlayerContext";

export const WebSocketContextObject = createContext<WebSocketContext>({
    sendChatMessage: (message: string, room_id: number) => { },
    chatMessages: [],
    lobbyState: null,
    gameState: null,
});

export function useWebSocketContext(): WebSocketContext {
    return useContext(WebSocketContextObject);
}

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
    const { player } = usePlayer()
    const {
        sendJsonMessage,
        lastJsonMessage,
    } = useWebSocket(WEBSOCKET_URL);

    const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
    const [lobbyState, setLobbyState] = useState<LobbyState | null>(null);
    const [gameState, setGameState] = useState<GameState | null>(null);

    useEffect(() => {
        if (lastJsonMessage === null) return

        const websocketMessage = JSON.parse(lastJsonMessage as string) as WebSocketMessage;
        switch (websocketMessage.type) {
            case "chat":
                setChatMessages((prevChatMessages) => {
                    const tempMessages = [...prevChatMessages, websocketMessage.payload as ChatMessage];
                    if (tempMessages.length > 10) {
                        tempMessages.shift()
                    }
                    return tempMessages;
                });
                break;
            case "lobby_state":
                setLobbyState(websocketMessage.payload as LobbyState);
                break;
            case "game_state":
                setGameState(websocketMessage.payload as GameState);
                break;
        }
    }, [lastJsonMessage]);

    function sendChatMessage(message: string, room_id: number) {
        const websocketMessage = {
            type: "chat",
            payload: {
                player_name: player?.name,
                room_id: room_id,
                content: message,
            },
        } as WebSocketMessage
        sendJsonMessage(websocketMessage);
    }

    return (
        <WebSocketContextObject.Provider value={{ sendChatMessage, chatMessages, lobbyState, gameState }}>
            {children}
        </WebSocketContextObject.Provider>
    );
}

