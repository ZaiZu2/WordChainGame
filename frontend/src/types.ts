import { UUID } from "crypto";

export type Room = {
    id?: number;
    name: string;
    players_no: number;
    capacity: number;
    status: "Open" | "Closed" | "Private"
    rules: object;
};

export type RoomIn = {
    name: string
    capacity: number
    rules: Record<string, any>
}


export type Player = {
    id?: UUID;
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
    detail?: string; // ['user with this name already exists', ...]
    query?: Record<string, string[]>; // 'page': ['must be a number', 'must be positive']
    path?: Record<string, string[]>; // 'id': ['must be a UUID', 'must be a valid UUID']
    cookie?: Record<string, string[]>; // ...
    body?: Record<string, string[]>; // ...
};

export type PlayerContext = {
    player: Player | null | undefined;
    logIn: (id: UUID) => void;
    logOut: () => void;
};

export type ChatMessage = {
    id?: number
    created_on?: Date
    content: string
    player_name: string
    room_id: number
}

export type GameState = {
}

export type RoomState = {
    room_id: number
    players: Record<string, Player>
}

export type LobbyState = {
    players: Record<string, Player>
    rooms: Record<number, Room>
}

export type ConnectionState = {
    code: number
    reason: string
}

export type WebSocketMessage = {
    type: 'chat' | 'game_state' | 'lobby_state' | 'room_state' | 'connection_state'
    payload: ChatMessage | GameState | LobbyState | RoomState | ConnectionState
}

export type Word = {
    id?: number
    content: string
    is_correct: boolean
    created_on: Date
    game_id: number
    player_name: string
}