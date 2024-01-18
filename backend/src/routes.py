from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import src.models as d  # d - database
import src.schemas as s  # s - schema
from src.models import get_db, get_user

app = FastAPI()

origins = ['http://localhost:3000']
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/players/me', status_code=status.HTTP_200_OK)
async def get_player(player: d.Player = Depends(get_user)) -> s.MePlayer:
    return player


@app.post('/players')
async def create_player(
    name: str, db: AsyncSession = Depends(get_db)) -> s.MePlayer:
    if await db.scalar(select(d.Player).where(d.Player.name == name)):
        raise HTTPException(status_code=409,
                            detail=f'Player with name {name} already exists')

    player = d.Player(name=name)
    db.add(player)
    await db.flush()
    await db.refresh(player)
    return player


@app.put('/players')
async def update_player(
    name: str, player: d.Player = Depends(get_user), db: AsyncSession = Depends(get_db)
) -> s.MePlayer:
    if await db.scalar(select(d.Player).where(d.Player.name == name)):
        raise HTTPException(
            status_code=409, detail=f'Player with name {name} already exists'
        )

    player.name = name
    db.add(player)
    await db.commit()
    return player


@app.get('/game_rooms')
async def get_game_rooms() -> list[s.GameRoom]:
    return []


@app.post('/game_rooms')
async def create_game_room(
    new_game_room: s.NewGameRoom,
    player: d.Player = Depends(get_user),
    db: AsyncSession = Depends(get_db),
) -> s.GameRoom:
    game = select(d.GameRoom).where(d.GameRoom.name == new_game_room.name)
    if await db.scalar(game):
        raise HTTPException(
            status_code=409,
            detail=f'Game room with name {new_game_room.name} already exists',
        )

    game_room = d.GameRoom(**new_game_room.model_dump(exclude_unset=True))
    game_room.owner = player
    db.add(game_room)
    await db.commit()
    return game_room
