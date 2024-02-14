import useWebSocket, { ReadyState } from "react-use-websocket"
import React, { createContext, useContext, useState, useEffect } from 'react'
import { WebSocketContext, WebSocketMessage, ChatMessage, LobbyState, GameState, ConnectionState, Room } from "@/types"
import { WEBSOCKET_URL } from '../config'
import { usePlayer } from "../contexts/PlayerContext"
import { CHAT_MESSAGE_LIMIT } from "../config"

export const WebSocketContextObject = createContext<WebSocketContext>({
    sendChatMessage: (message: string, room_id: number) => { },
    chatMessages: [],
    rooms: {},
    gameState: null,
})

export function useWebSocketContext(): WebSocketContext {
    return useContext(WebSocketContextObject);
}

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
    const { logOut, player } = usePlayer()
    const {
        sendJsonMessage,
        lastJsonMessage,
    } = useWebSocket(WEBSOCKET_URL, {});

    const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
    const [rooms, setRooms] = useState<Record<number, Room>>({});
    const [gameState, setGameState] = useState<GameState | null>(null);

    useEffect(function parseMessage() {
        if (lastJsonMessage === null) return

        const websocketMessage = JSON.parse(lastJsonMessage as string) as WebSocketMessage;
        switch (websocketMessage.type) {
            case "chat":
                setChatMessages((prevChatMessages) => {
                    const tempMessages = [...prevChatMessages, websocketMessage.payload as ChatMessage];
                    if (tempMessages.length > CHAT_MESSAGE_LIMIT) {
                        tempMessages.shift()
                    }
                    return tempMessages;
                });
                break;
            case "lobby_state":
                setRooms((prevRooms) => {
                    const lobbyState = websocketMessage.payload as LobbyState;
                    const newRooms = lobbyState.rooms;
                    return { ...prevRooms, ...newRooms }
                });
                console.log(websocketMessage.payload);
                break;
            case "game_state":
                setGameState(websocketMessage.payload as GameState);
                break;
            case "connection_state":
                const connState = websocketMessage.payload as ConnectionState;
                console.log(connState);
                if (connState.code === 4001) {
                    // TODO: Show toast saying that the player can only use one client at a time
                    logOut();
                }
                break;
        }
    }, [lastJsonMessage, logOut]);

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
        <WebSocketContextObject.Provider value={{ sendChatMessage, chatMessages, rooms, gameState }}>
            {children}
        </WebSocketContextObject.Provider>
    );
}

