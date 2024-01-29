import { BASE_API_URL } from "../config";
import { ApiResponse, RequestOptions, ValidatedFields } from "../types";
import { createContext, useContext } from "react";
import { ConnectionError, ApiError } from "../errors";

class ApiClient {
    private BASE_API_URL: string;

    constructor() {
        this.BASE_API_URL = BASE_API_URL;
    }

    async request<T>(url: string | URL, options: RequestOptions): Promise<ApiResponse<T>> {
        let query = new URLSearchParams(options.query || {}).toString();
        if (query !== "") {
            query = "?" + query;
        }

        return fetch(`${this.BASE_API_URL}/${url}${query}`, {
            method: options.method,
            headers: {
                "Content-Type": "application/json",
                ...options.headers,
            },
            body: options.body ? JSON.stringify(options.body) : null,
        })
            .catch(() => {
                throw new ConnectionError();
            })
            .then(async (response): Promise<ApiResponse<T>> => {
                const json: T | ValidatedFields = await response.json();

                if (response.ok) {
                    return {
                        status: response.status,
                        body: json as T,
                    };
                } else {
                    const errorMessages = await this.extractErrorMessages(json as ValidatedFields);
                    console.log(errorMessages);
                    throw new ApiError(response.status, errorMessages);
                }
            });
    }

    async get<T>(
        url: string | URL,
        query?: Record<string, string>,
        options?: {
            headers?: Record<string, string>;
            cookies?: Record<string, string>;
        }
    ): Promise<ApiResponse<T>> {
        return this.request(url, { method: "GET", query, ...options });
    }

    async post<T>(
        url: string | URL,
        query?: Record<string, string>,
        body?: any,
        options?: {
            headers?: Record<string, string>;
            cookies?: Record<string, string>;
        }
    ): Promise<ApiResponse<T>> {
        return this.request(url, { method: "POST", query, body, ...options });
    }

    async put<T>(
        url: string | URL,
        query?: Record<string, string>,
        body?: any,
        options?: {
            headers?: Record<string, string>;
            cookies?: Record<string, string>;
        }
    ): Promise<ApiResponse<T>> {
        return this.request(url, { method: "PUT", query, body, ...options });
    }

    async delete<T>(
        url: string | URL,
        query?: Record<string, string>,
        options?: {
            headers?: Record<string, string>;
            cookies?: Record<string, string>;
        }
    ): Promise<ApiResponse<T>> {
        return this.request(url, { method: "DELETE", query, ...options });
    }

    private async extractErrorMessages(validatedFields: ValidatedFields) {
        let errorMessages: Record<string, string[]> = {};

        for (const fields of Object.values(validatedFields)) {
            if (Array.isArray(fields)) {
                errorMessages = { ...errorMessages, ...{ detail: fields } };
            } else {
                for (const [fieldName, fieldMessages] of Object.entries(fields)) {
                    errorMessages = {
                        ...errorMessages,
                        ...{ [fieldName]: fieldMessages },
                    };
                }
            }
        }

        return errorMessages;
    }
}

const api = new ApiClient();
const ApiContext = createContext(api);

export function useApi() {
    return useContext(ApiContext);
}

export default function ApiProvider({ children }: { children: React.ReactNode }) {
    return <ApiContext.Provider value={api}>{children}</ApiContext.Provider>;
}
