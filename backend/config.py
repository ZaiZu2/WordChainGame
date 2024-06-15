import json
from functools import lru_cache
from pathlib import Path
from uuid import UUID

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    class Config:
        env_file = Path(__file__).parent.resolve() / '.env'
        env_file_encoding = 'utf-8'

    DATABASE_URI: str
    CORS_ORIGINS: list[str]

    AUTH_COOKIE_NAME: str = 'player_id'
    AUTH_COOKIE_EXPIRATION: int = 1200  # seconds

    DICTIONARY_API_KEY: str
    DICTIONARY_API_URL: str = 'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{word}?key={api_key}'

    GAME_START_DELAY: int = 1  # seconds, Delay game start to prime the players
    TURN_START_DELAY: int = 1  # seconds, Delay each turn start to prime the players
    MAX_TURN_TIME_DEVIATION: float = 0.1  # seconds

    ROOM_DELETION_INTERVAL: int = 60  # seconds
    ROOM_DELETION_DELAY: int = 180  # seconds

    ROOT_ID: UUID
    ROOT_NAME: str = 'root'
    LOBBY_ID: int = 1
    LOBBY_NAME: str = 'lobby'


@lru_cache
def get_config() -> Config:
    return Config()  # type: ignore


with open(Path(__file__).parent / 'logging_config.json') as f:
    LOGGING_CONFIG = json.load(f)
