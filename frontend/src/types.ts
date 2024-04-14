import { UUID } from "crypto";

export type RoomOut = {
    id?: number;
    name: string;
    players_no: number;
    capacity: number;
    status: "Open" | "Closed" | "Private";
    rules: DeathmatchRules;
    owner_name: string;
};

export type RoomIn = {
    name: string;
    capacity: number;
    rules: DeathmatchRules;
};

export type Player = {
    id?: UUID;
    name: string;
    created_on: Date;
};

export type RoomPlayer = Player & {
    ready: boolean;
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

export type ChatMessage = {
    id?: number;
    created_on?: Date;
    content: string;
    player_name: string;
    room_id: number;
};

export type GamePlayer = {
    name: string;
    score: number;
    mistakes: number;
};

export type GameInput = {
    game_id: number;
    type: "word_input";
    word: string;
};

export type Word = {
    content: string;
    is_correct?: boolean;
    description?: Record<string, string>;
};

export type Turn = {
    word: Word | null;
    is_correct: boolean | null;
    started_on: string;
    ended_on: string | null;
    current_player_idx: number;
};

type StartGameState = {
    type_: "start_game";
    id: number;
    status: "In progress";
    players: GamePlayer[];
    lost_players: GamePlayer[];
    rules: DeathmatchRules;
};

type EndGameState = {
    type_: "end_game";
    status: "Finished";
};

type StartTurnState = {
    type_: "start_turn";
    current_turn: Turn;
};

type EndTurnState = {
    type_: "end_turn";
    players: GamePlayer[];
    lost_players: GamePlayer[];
    current_turn: Turn;
};

export type GameState = StartGameState | EndGameState | StartTurnState | EndTurnState;

export type RoomState = Omit<RoomOut, "players_no"> & {
    players: Record<string, RoomPlayer>;
};

export type DeathmatchRules = {
    type: "deathmatch";
    round_time: number;
    start_score: number;
    penalty: number; // should be less than or equal to 0
    reward: number; // should be greater than or equal to 0
};

export type LobbyState = {
    players: Record<string, Player>;
    rooms: Record<number, RoomOut>;
    stats: CurrentStatistics;
};

export type CurrentStatistics = {
    active_players: number;
    active_rooms: number;
};

export type AllTimeStatistics = {
    longest_chain: number;
    longest_game_time: number;
    total_games: number;
};

export type ConnectionState = {
    code: number;
    reason: string;
};

export type WebSocketMessage = {
    type: "chat" | "game_state" | "lobby_state" | "room_state" | "connection_state";
    payload: ChatMessage | GameState | LobbyState | RoomState | ConnectionState;
};

export type ModalConfigs = {
    roomRules?: RoomRulesConfig;
};

export type RoomRulesConfig = {
    defaultValues?: RoomIn;
    disabledFields?: "name"[];
    onSubmit: "PUT" | "POST";
};
