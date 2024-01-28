import { UUID } from "crypto";

export type GameRoom = {
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

export type ResponseOk<T> = {
    ok: true;
    status: number;
    body: T;
};

export type ResponseError = {
    ok: false;
    status: number;
    errors: Record<string, string[]>;
};

export type ValidatedFields = {
    detail?: string[]; // ['user with this name already exists', ...]
    query?: Record<string, string[]>; // 'page': ['must be a number', 'must be positive']
    path?: Record<string, string[]>; // 'id': ['must be a UUID', 'must be a valid UUID']
    body?: Record<string, string[]>; // ...
};

export type PlayerContext = {
    player: MePlayer | null | undefined;
    logIn: (player: MePlayer) => void;
    logOut: () => void;
};
