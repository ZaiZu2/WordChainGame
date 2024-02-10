const _BASE_API_URL = process.env.REACT_APP_BASE_API_URL;
if (typeof _BASE_API_URL === 'undefined') {
    throw new Error('REACT_APP_BASE_API_URL is undefined');
}
export const BASE_API_URL = _BASE_API_URL;

const _WEBSOCKET_URL = process.env.REACT_APP_WEBSOCKET_URL;
if (typeof _WEBSOCKET_URL === 'undefined') {
    throw new Error('REACT_APP_WEBSOCKET_URL is undefined');
}
export const WEBSOCKET_URL = _WEBSOCKET_URL;

export const CHAT_MESSAGE_LIMIT = 30