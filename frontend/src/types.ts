import { UUID } from "crypto";

export type Room = {
    id: number;
    name: string;
    rules: object;
};

export type MePlayer = {
    id: UUID;
    name: string;
    created_on: Date;
};

export type RequestOptions = {
    method: "GET" | "POST" | "PUT" | "DELETE";
    headers?: Record<string, string>;
    query?: Record<string, string>;
    body?: any;
};

export type ApiResponse<T> = {
    status: number;
    body: T;
};

export type ValidatedFields = {
    detail?: string[]; // ['user with this name already exists', ...]
    query?: Record<string, string[]>; // 'page': ['must be a number', 'must be positive']
    path?: Record<string, string[]>; // 'id': ['must be a UUID', 'must be a valid UUID']
    cookie?: Record<string, string[]>; // ...
    body?: Record<string, string[]>; // ...
};

export type PlayerContext = {
    player: MePlayer | null | undefined;
    logIn: (id: UUID) => void;
    logOut: () => void;
};

export type ChatMessage = {
    player_name: string
    room_id: number
    created_on?: Date
    content: string
}

export type GameState = {
}

export type LobbyState = {
    rooms: Room[]
}

export type WebSocketMessage = {
    type: 'chat' | 'game_state' | 'lobby_state'
    payload: ChatMessage | GameState | LobbyState
}


export type WebSocketContext = {
    sendChatMessage: (message: string, room_id: number) => void;
    chatMessages: ChatMessage[];
    lobbyState: LobbyState | null;
    gameState: GameState | null;
}