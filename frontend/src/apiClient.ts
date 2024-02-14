import { BASE_API_URL } from "./config";
import { ApiResponse, RequestOptions, ValidatedFields } from "./types";
import { ConnectionError, ApiError, AuthError } from "./errors";

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

        return fetch(`${this.BASE_API_URL}${url}${query}`, {
            method: options.method,
            credentials: "include", // Include http-only auth cookie
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
                } else if (response.status === 403) {
                    const errorMessages = await this.extractErrorMessages(json as ValidatedFields);
                    throw new AuthError(response.status, errorMessages);
                } else {
                    const errorMessages = await this.extractErrorMessages(json as ValidatedFields);
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
        options?: {
            query?: Record<string, string>,
            body?: any,
            headers?: Record<string, string>;
            cookies?: Record<string, string>;
        }
    ): Promise<ApiResponse<T>> {
        return this.request(url, { method: "POST", ...options });
    }

    async put<T>(
        url: string | URL,
        options?: {
            query?: Record<string, string>,
            body?: any,
            headers?: Record<string, string>;
            cookies?: Record<string, string>;
        }
    ): Promise<ApiResponse<T>> {
        return this.request(url, { method: "PUT", ...options });
    }

    async delete<T>(
        url: string | URL,
        options?: {
            query?: Record<string, string>,
            headers?: Record<string, string>;
            cookies?: Record<string, string>;
        }
    ): Promise<ApiResponse<T>> {
        return this.request(url, { method: "DELETE", ...options });
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

const apiClient = new ApiClient();
export default apiClient;