import { UUID } from "crypto";

export type RoomOut = {
    id?: number;
    name: string;
    players_no: number;
    capacity: number;
    status: "Open" | "Closed" | "In progress";
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
};

export type RoomPlayer = Player & {
    ready: boolean;
    in_game: boolean;
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
    in_game: boolean;
    score: number;
    mistakes: number;
    place: number;
};

export type Word = {
    content: string;
    is_correct?: boolean;
    description?: [string, string][];
};

export type Turn = {
    word: Word | null;
    is_correct: boolean | null;
    info: string;
    started_on: string;
    ended_on: string;
    player_idx: number;
};

type StartGameState = {
    state: "STARTED";
    id: number;
    status: "Starting";
    players: GamePlayer[];
    lost_players: GamePlayer[];
    rules: DeathmatchRules;
};

type EndGameState = {
    state: "ENDED";
    status: "Finished";
};

type WaitState = {
    state: "WAITING";
};

type StartTurnState = {
    state: "STARTED_TURN";
    current_turn: Turn;
    status?: "In progress";
};

type EndTurnState = {
    state: "ENDED_TURN";
    players: GamePlayer[];
    lost_players: GamePlayer[];
    current_turn: Turn;
};

export type GameState = StartGameState | EndGameState | WaitState | StartTurnState | EndTurnState;

export type WordInput = {
    input_type: "word_input";
    game_id: number;
    word: string;
};

export type GameInput = WordInput;

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

export type KickPlayerAction = {
    action: "KICK_PLAYER";
};

export type Action = KickPlayerAction;

export type WebSocketMessage =
    | { payload: ChatMessage & { type_: "chat" } }
    | { payload: GameState & { type_: "game_state" } }
    | { payload: LobbyState & { type_: "lobby_state" } }
    | { payload: RoomState & { type_: "room_state" } }
    | { payload: ConnectionState & { type_: "connection_state" } }
    | { payload: GameInput & { type_: "game_input" } }
    | { payload: Action & { type_: "action" } };

export type ModalConfigs = {
    roomRules?: RoomRulesConfig;
};

export type RoomRulesConfig = {
    defaultValues?: RoomIn;
    disabledFields?: "name"[];
    onSubmit: "PUT" | "POST";
};
