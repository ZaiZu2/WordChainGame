from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from enum import Enum

app = FastAPI()

# Define a list of origins that should be allowed (you can use '*' to allow all)
origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)


class GameStatusEnum(str, Enum):
    IN_PROGRESS = 'In progress'
    OPEN = 'Open'
    CLOSED = 'Closed'


class GameRoom(BaseModel):
    id_: int
    name: str
    player_ids: list[int]
    max_size: int
    status: GameStatusEnum


@app.get("/games")
async def games() -> list[GameRoom]:
    game_1 = GameRoom(id_=1,
                      name='Game 1',
                      player_ids=[1, 2, 3, 4],
                      max_size=5,
                      status=GameStatusEnum.IN_PROGRESS)
    game_2 = GameRoom(id_=2,
                      name='Game 2',
                      player_ids=[5, 6],
                      max_size=5,
                      status=GameStatusEnum.OPEN)
    game_3 = GameRoom(id_=3,
                      name='Game 3',
                      player_ids=[],
                      max_size=5,
                      status=GameStatusEnum.OPEN)

    return [game_1, game_2, game_3]
