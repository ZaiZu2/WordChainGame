from functools import lru_cache

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

    SECRET_KEY: str
    DATABASE_URI: str

    AUTH_COOKIE_NAME: str = 'player_id'
    AUTH_COOKIE_EXPIRATION: int = 1200  # seconds


@lru_cache
def get_config() -> Config:
    return Config()


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
            'handlers': ['requests_to_file', 'requests_to_stream'],
            'level': 'INFO',
            'propagate': False,
        },
        'uvicorn': {
            'handlers': ['errors_to_file', 'errors_to_stream'],
            'level': 'INFO',
            'propagate': False,
        },
        'uvicorn.error': {
            'handlers': ['errors_to_file', 'errors_to_stream'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'version': 1,
}
