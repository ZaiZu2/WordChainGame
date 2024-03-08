
export class ConnectionError extends Error {
    constructor() {
        super("Connection was lost");
        this.name = "ConnectionError";

        // This line is needed to restore the correct prototype chain.
        Object.setPrototypeOf(this, new.target.prototype);
    }
}

export class ApiError extends Error {
    messages: string[];
    status: number;

    constructor(status: number, errorMessages: string[]) {
        super(`API request failed with status code ${status}`);
        this.name = "ApiError";
        this.status = status;
        this.messages = errorMessages;

        // This line is needed to restore the correct prototype chain.
        Object.setPrototypeOf(this, new.target.prototype);
    }
}

export class AuthError extends Error {
    errors: string[];
    status: number;

    constructor(status: number, errorMessages: string[]) {
        super("Player is not authenticated");
        this.name = "AuthError";
        this.status = status;
        this.errors = errorMessages;

        // This line is needed to restore the correct prototype chain.
        Object.setPrototypeOf(this, new.target.prototype);
    }
}
