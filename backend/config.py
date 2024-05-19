from functools import lru_cache
from pathlib import Path
from uuid import UUID

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    class Config:
        env_file = Path(__file__).parent.resolve() / '.env'
        env_file_encoding = 'utf-8'

    SECRET_KEY: str
    DATABASE_URI: str

    AUTH_COOKIE_NAME: str = 'player_id'
    AUTH_COOKIE_EXPIRATION: int = 1200  # seconds

    DICTIONARY_API_KEY: str
    DICTIONARY_API_URL: str = 'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{word}?key={api_key}'

    GAME_START_DELAY: int = 1  # seconds, Delay game start to prime the players
    TURN_START_DELAY: int = 1  # seconds, Delay each turn start to prime the players
    MAX_TURN_TIME_DEVIATION: float = 0.1  # seconds

    ROOM_DELETION_INTERVAL: int = 10  # seconds
    ROOM_DELETION_DELAY: int = 300  # seconds

    ROOT_ID: UUID
    ROOT_NAME: str = 'root'
    LOBBY_ID: int = 1
    LOBBY_NAME: str = 'lobby'


@lru_cache
def get_config() -> Config:
    return Config()  # type: ignore


LOGGING_CONFIG = {
    'disable_existing_loggers': False,
    'formatters': {
        'access_file': {
            '()': 'uvicorn.logging.AccessFormatter',
            'fmt': '%(levelprefix)s %(asctime)s %(client_addr)s %(request_line)s %(status_code)s',
            'use_colors': False,
        },
        'access_stream': {
            '()': 'uvicorn.logging.AccessFormatter',
            'fmt': '%(levelprefix)s %(asctime)s %(client_addr)s %(request_line)s %(status_code)s',
            'use_colors': True,
        },
        'default_file': {
            '()': 'uvicorn.logging.DefaultFormatter',
            'fmt': '%(levelprefix)s %(message)s',
            'use_colors': False,
        },
        'default_stream': {
            '()': 'uvicorn.logging.DefaultFormatter',
            'fmt': '%(levelprefix)s %(message)s',
            'use_colors': True,
        },
    },
    'handlers': {
        'requests_to_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'access_file',
            'filename': 'logs/requests.log',
            'maxBytes': 10240,
            'backupCount': 10,
        },
        'requests_to_stream': {
            'class': 'logging.StreamHandler',
            'formatter': 'access_stream',
            'stream': 'ext://sys.stdout',
        },
        'errors_to_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'default_file',
            'filename': 'logs/internal.log',
            'maxBytes': 10240,
            'backupCount': 10,
        },
        'errors_to_stream': {
            'class': 'logging.StreamHandler',
            'formatter': 'default_stream',
            'stream': 'ext://sys.stderr',
        },
    },
    'loggers': {
        'uvicorn.access': {
            'handlers': ['requests_to_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'uvicorn': {
            'handlers': [
                'errors_to_file',
            ],
            'level': 'INFO',
            'propagate': False,
        },
        'uvicorn.error': {
            'handlers': [
                'errors_to_file',
            ],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'version': 1,
}
