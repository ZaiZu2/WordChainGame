import useWebSocket, { ReadyState } from "react-use-websocket"
import React, { createContext, useContext, useState, useEffect } from 'react'
import { WebSocketMessage, ChatMessage, LobbyState, GameState, ConnectionState, Room, RoomState } from "@/types"
import { WEBSOCKET_URL } from '../config'
import { usePlayer } from "../contexts/PlayerContext"
import { CHAT_MESSAGE_LIMIT } from "../config"



export type WebSocketContext = {
    sendChatMessage: (message: string, room_id: number) => void;
    chatMessages: ChatMessage[];
    lobbyState: LobbyState | null;
    roomState: RoomState | null;
    gameState: GameState | null;
}

export const WebSocketContextObject = createContext<WebSocketContext>({
    sendChatMessage: (message: string, room_id: number) => { },
    chatMessages: [],
    lobbyState: null,
    roomState: null,
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
    const [lobbyState, setLobbyState] = useState<LobbyState | null>(null);
    const [roomState, setRoomState] = useState<RoomState | null>(null);
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
                setLobbyState((prevLobbyState) => {
                    const lobbyState = websocketMessage.payload as LobbyState;
                    if (prevLobbyState === null) {
                        return lobbyState;
                    } else {
                        // Run differential update on any object in the lobbyState
                        const players = { ...prevLobbyState.players, ...lobbyState.players };
                        const rooms = { ...prevLobbyState.rooms, ...lobbyState.rooms };
                        return { players, rooms };
                    }
                });
                break;

            case "room_state":
                setRoomState((prevRoomState) => {
                    const roomState = websocketMessage.payload as RoomState;
                    if (prevRoomState === null) {
                        return roomState;
                    } else {
                        // Run differential update on any object in the roomState
                        const players = { ...prevRoomState.players, ...roomState.players };
                        return { ...prevRoomState, ...roomState, players };
                    }
                });
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
        <WebSocketContextObject.Provider value={{ sendChatMessage, chatMessages, lobbyState, roomState, gameState }}>
            {children}
        </WebSocketContextObject.Provider>
    );
}

