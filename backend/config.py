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
