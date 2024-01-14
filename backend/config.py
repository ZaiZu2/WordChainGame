from functools import lru_cache

from pydantic import BaseSettings


class Config(BaseSettings):
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

    SECRET_KEY: str
    DATABASE_URI: str


@lru_cache
def get_config() -> Config:
    return Config()
