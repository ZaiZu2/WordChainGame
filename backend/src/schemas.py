from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class MePlayer(BaseModel):
    id_: UUID
    name: str
    created_on: datetime


class GameRoom(BaseModel):
    id_: int
    name: str
    rules: dict


class NewGameRoom(BaseModel):
    name: str
    rules: dict
