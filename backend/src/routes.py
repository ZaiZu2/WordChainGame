from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Response, WebSocket, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import src.models as d  # d - database
import src.schemas as s  # s - schema
from src.connection_manager import ConnectionManager, get_connection_manager
from src.fastapi_utils import TagsEnum
from src.models import get_db, get_player, set_auth_cookie

router = APIRouter(tags=[TagsEnum.ALL])


@router.get('/players/me', status_code=status.HTTP_200_OK)
async def get_player(player: Annotated[d.Player, Depends(get_player)]) -> s.MePlayer:
    return player


@router.post('/players', status_code=status.HTTP_201_CREATED)
async def create_player(
    name: Annotated[str, Body(embed=True, max_length=10)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> s.MePlayer:
    if await db.scalar(select(d.Player).where(d.Player.name == name)):
        raise HTTPException(
            status_code=409, detail=[f'Player with name {name} already exists']
        )

    player = d.Player(name=name)
    db.add(player)
    await db.flush()
    await db.refresh(player)

    return s.MePlayer.model_validate(player)


@router.post('/players/login', status_code=status.HTTP_200_OK)
async def login_player(
    id_: Annotated[UUID, Body(embed=True, alias='id')],
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> s.MePlayer:
    player = await db.scalar(select(d.Player).where(d.Player.id_ == id_))
    if not player:
        raise HTTPException(status.HTTP_403_FORBIDDEN, 'Player not found')

    await set_auth_cookie(player.id_, response)
    return s.MePlayer.model_validate(player)


@router.post('/players/logout', status_code=status.HTTP_200_OK)
async def logout_player(
    response: Response, player: Annotated[d.Player, Depends(get_player)]
) -> None:
    await set_auth_cookie('', response)


@router.put('/players', status_code=status.HTTP_200_OK)
async def update_player(
    name: Annotated[str, Body(embed=True)],
    player: Annotated[d.Player, Depends(get_player)],
    db: Annotated[AsyncSession, Depends(get_db)],
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


@router.get('/rooms', status_code=status.HTTP_200_OK)
async def get_rooms(
    player: Annotated[d.Player, Depends(get_player)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[s.Room]:
    rooms = await db.scalars(select(d.Room))
    return [s.Room.model_validate(room) for room in rooms]


@router.post('/rooms', status_code=status.HTTP_201_CREATED)
async def create_room(
    new_room: s.NewRoom,
    player: Annotated[d.Player, Depends(get_player)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> s.Room:
    game = select(d.Room).where(d.Room.name == new_room.name)
    if await db.scalar(game):
        raise HTTPException(
            status_code=409,
            detail=f'Game room with name {new_room.name} already exists',
        )

    room = d.Room(**new_room.model_dump(exclude_unset=True))
    room.owner = player
    db.add(room)
    await db.commit()
    return room


@router.websocket('room/{room_id}/chat')
async def connect_to_chat(
    room_id: int,
    websocket: WebSocket,
    player: Annotated[d.Player, Depends(get_player)],
    db: Annotated[AsyncSession, Depends(get_db)],
    conn_manager: Annotated[ConnectionManager, Depends(get_connection_manager)],
) -> None:
    await websocket.accept()
    await conn_manager.add_connection(player.id_, room_id, websocket)

    while True:
        message_string = await websocket.receive_text()
        await conn_manager.broadcast(room_id, message_string)

        message = d.Message(content=message_string, room_id=room_id, player=player)
        db.add(message)
        await db.commit()
