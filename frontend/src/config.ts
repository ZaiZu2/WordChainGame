const _BASE_API_URL = process.env.REACT_APP_BASE_API_URL;
if (typeof _BASE_API_URL === "undefined") {
    throw new Error("REACT_APP_BASE_API_URL is undefined");
}
export const BASE_API_URL = _BASE_API_URL;

const _WEBSOCKET_URL = process.env.REACT_APP_WEBSOCKET_URL;
if (typeof _WEBSOCKET_URL === "undefined") {
    throw new Error("REACT_APP_WEBSOCKET_URL is undefined");
}
export const WEBSOCKET_URL = _WEBSOCKET_URL;

export const CHAT_MESSAGE_LIMIT = 30;
export const WORD_LIST_LENGTH = 6;
export const WORD_LIST_MAX_WORD_SIZE = 1.75; // rem
export const TURN_START_DELAY = 1;
export const GAME_START_DELAY = 1;
