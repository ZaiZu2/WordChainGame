import { BASE_API_URL } from "../config";

import {
    ResponseOk,
    ResponseError,
    RequestOptions,
    ValidatedFields,
} from "../types";

import { createContext, useContext } from "react";

class ApiClient {
    private BASE_API_URL: string;

    constructor() {
        this.BASE_API_URL = BASE_API_URL;
    }

    async request<T>(
        url: string | URL,
        options: RequestOptions
    ): Promise<ResponseOk<T> | ResponseError> {
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
            .then(async (response): Promise<ResponseOk<T> | ResponseError> => {
                const json: T | ValidatedFields = await response.json();

                return response.ok
                    ? {
                          ok: response.ok,
                          status: response.status,
                          body: json as T,
                      }
                    : {
                          ok: response.ok,
                          status: response.status,
                          errors: await this.extractErrorMessages(
                              json as ValidatedFields
                          ),
                      };
            })
            .catch(() => {
                return {
                    ok: false,
                    status: 500,
                    errors: { detail: ["Connection was lost"] },
                };
            });
    }

    async get<T>(
        url: string | URL,
        query: Record<string, string>,
        options: {
            headers?: Record<string, string>;
            cookies?: Record<string, string>;
        }
    ): Promise<ResponseOk<T> | ResponseError> {
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
    ): Promise<ResponseOk<T> | ResponseError> {
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
    ): Promise<ResponseOk<T> | ResponseError> {
        return this.request(url, { method: "PUT", query, body, ...options });
    }

    async delete<T>(
        url: string | URL,
        query?: Record<string, string>,
        options?: {
            headers?: Record<string, string>;
            cookies?: Record<string, string>;
        }
    ): Promise<ResponseOk<T> | ResponseError> {
        return this.request(url, { method: "DELETE", query, ...options });
    }

    private async extractErrorMessages(validatedFields: ValidatedFields) {
        let errorMessages: Record<string, string[]> = {};

        for (const fields of Object.values(validatedFields)) {
            if (Array.isArray(fields)) {
                errorMessages = { ...errorMessages, ...{ detail: fields } };
            } else {
                for (const [fieldName, fieldMessages] of Object.entries(
                    fields
                )) {
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

export default function ApiProvider({
    children,
}: {
    children: React.ReactNode;
}) {
    return <ApiContext.Provider value={api}>{children}</ApiContext.Provider>;
}
