import { BASE_API_URL } from "../config"

import { ResponseObject, RequestOptions } from "../types"

import { createContext, useContext } from "react"

class GameApiClient {
    private BASE_API_URL: string;

    constructor() {
        this.BASE_API_URL = BASE_API_URL
    }


    async request<T>(options: RequestOptions): Promise<ResponseObject<T>> {
        let query = new URLSearchParams(options.query || {}).toString();
        if (query !== '') {
            query = '?' + query;
        }

        let response;
        try {
            response = await fetch(this.BASE_API_URL + options.url + query, {
                method: options.method,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers,
                },
                body: options.body ? JSON.stringify(options.body) : null,
            });
        }
        catch (error: unknown) {
            response = {
                ok: false,
                status: 500,
                body: async () => {
                    return {
                        code: 500,
                        message: 'The server is unresponsive',
                        description: error.toString(),
                    };
                }
            };
        }

        return {
            ok: response.ok,
            status: response.status,
            body: response.status !== 204 ? await response.json() : null
        };
    }
}

const api = new GameApiClient();
const ApiContext = createContext(api);

export default function ApiClient({ children }: { children: React.ReactNode }) {
    return (
        <ApiContext.Provider value={api}>
            {children}
        </ApiContext.Provider>
    )
}

export function useApi() {
    return useContext(ApiContext);
}
