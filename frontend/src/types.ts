export type GameRoom = {
    id: number,
    name: string,
    rules: object,
}


export type RequestOptions = {
    method: string;
    url: string;
    headers?: Record<string, string>;
    body?: any;
    query?: Record<string, string>;
};

export type ResponseObject<T = any> = {
    ok: boolean;
    status: number;
    body?: T | null;
};