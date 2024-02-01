
export class ConnectionError extends Error {
    constructor() {
        super("Connection was lost");
        this.name = "ConnectionError";

        // This line is needed to restore the correct prototype chain.
        Object.setPrototypeOf(this, new.target.prototype);
    }
}

export class ApiError extends Error {
    errorMessages: Record<string, any>;
    status: number;

    constructor(status: number, errorMessages: Record<string, string[]>) {
        super(`API request failed with status code ${status}`);
        this.name = "ApiError";
        this.status = status;
        this.errorMessages = errorMessages;

        // This line is needed to restore the correct prototype chain.
        Object.setPrototypeOf(this, new.target.prototype);
    }
}

export class AuthError extends Error {
    errorMessages: Record<string, any>;
    status: number;

    constructor(status: number, errorMessages: Record<string, string[]>) {
        super("Player is not authenticated");
        this.name = "AuthError";
        this.status = status;
        this.errorMessages = errorMessages;

        // This line is needed to restore the correct prototype chain.
        Object.setPrototypeOf(this, new.target.prototype);
    }
}
