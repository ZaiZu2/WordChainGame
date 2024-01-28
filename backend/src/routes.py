from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import src.models as d  # d - database
import src.schemas as s  # s - schema
from src.fastapi_utils import TagsEnum
from src.models import get_db, get_user

router = APIRouter(tags=[TagsEnum.ALL])


@router.get('/players/me', status_code=status.HTTP_200_OK)
async def get_player(player: d.Player = Depends(get_user)) -> s.MePlayer:
    return player


@router.post('/players', status_code=status.HTTP_201_CREATED)
async def create_player(
    name: Annotated[str, Query(max_length=10)], db: AsyncSession = Depends(get_db)
) -> s.MePlayer:
    if await db.scalar(select(d.Player).where(d.Player.name == name)):
        raise HTTPException(
            status_code=409, detail=[f'Player with name {name} already exists']
        )

    player = d.Player(name=name)
    db.add(player)
    await db.flush()
    await db.refresh(player)
    return s.MePlayer.from_orm(player)


@router.put('/players', status_code=status.HTTP_200_OK)
async def update_player(
    name: str, player: d.Player = Depends(get_user), db: AsyncSession = Depends(get_db)
) -> s.MePlayer:
    if await db.scalar(select(d.Player).where(d.Player.name == name)):
        raise HTTPException(
            status_code=409, detail=[f'Player with name {name} already exists']
        )

    player.name = name
    db.add(player)
    await db.flush()
    await db.refresh(player)
    return player


@router.get('/game_rooms', status_code=status.HTTP_200_OK)
async def get_game_rooms() -> list[s.GameRoom]:
    return []


@router.post('/game_rooms', status_code=status.HTTP_201_CREATED)
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
