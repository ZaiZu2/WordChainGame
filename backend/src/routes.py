import asyncio
from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    Response,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import src.models as d  # d - database
import src.schemas as s  # s - schema
from src.connection_manager import ConnectionManager
from src.dependencies import (
    get_connection_manager,
    get_db,
    get_player,
    set_auth_cookie,
)
from src.helpers import (
    TagsEnum,
    accept_websocket_connection,
    handle_player_disconnect,
    listen_for_messages,
    move_player_and_broadcast,
    send_initial_state,
)

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
async def update_player_name(
    name: Annotated[str, Body(embed=True)],
    player: Annotated[d.Player, Depends(get_player)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> s.MePlayer:
    if db.scalar(select(d.Player).where(d.Player.name == name)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=[f'Player with name {name} already exists'],
        )

    player.name = name
    db.add(player)
    await db.flush()
    await db.refresh(player)
    return player


# @router.get('/rooms', status_code=status.HTTP_200_OK)
# async def get_rooms(
#     player: Annotated[d.Player, Depends(get_player)],
#     db: Annotated[AsyncSession, Depends(get_db)],
# ) -> list[s.Room]:
#     # Room with id 1 is the lobby
#     rooms = await db.scalars(select(d.Room).where(d.Room.id_ != 1))
#     return [s.Room.model_validate(room) for room in rooms]


@router.post('/rooms', status_code=status.HTTP_201_CREATED)
async def create_room(
    room_in: s.RoomIn,
    player: Annotated[d.Player, Depends(get_player)],
    db: Annotated[AsyncSession, Depends(get_db)],
    conn_manager: Annotated[ConnectionManager, Depends(get_connection_manager)],
):
    if await db.scalar(select(d.Room).where(d.Room.name == room_in.name)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'Game room with name {room_in.name} already exists',
        )

    room = d.Room(**room_in.model_dump(exclude_unset=True))
    room.owner = player
    db.add(room)
    await db.flush([room])

    room_out = s.RoomOut(players_no=0, **room.to_dict())
    lobby_state = s.LobbyState(rooms={room.id_: room_out})
    await conn_manager.broadcast_lobby_state(lobby_state)


@router.post('/rooms/{room_id}/join', status_code=status.HTTP_200_OK)
async def join_room(
    room_id: int,
    player: Annotated[d.Player, Depends(get_player)],
    db: Annotated[AsyncSession, Depends(get_db)],
    conn_manager: Annotated[ConnectionManager, Depends(get_connection_manager)],
):
    room = await db.scalar(
        select(d.Room)
        .where(d.Room.id_ == room_id)
        .options(selectinload(d.Room.players))
    )
    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Room does not exist'
        )
    if room.status != d.RoomStatusEnum.OPEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail='Room is not accessible'
        )
    if len(room.players) >= room.capacity:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail='Room is full'
        )

    old_room_id = player.room_id
    player.room = room
    await db.flush([player])
    move_player_and_broadcast(player, old_room_id, db, conn_manager)

    players_out = {
        room_player.id_: s.PlayerOut(**room_player.to_dict())
        for room_player in room.players
    }
    room_state = s.RoomState(players=players_out)
    await conn_manager.broadcast_room_state(room.id_, room_state)

    # TODO: Collect chat history and send it to the player


@router.websocket('/connect')
async def connect(
    websocket: WebSocket,
    player: Annotated[d.Player, Depends(get_player)],
    db: Annotated[AsyncSession, Depends(get_db)],
    conn_manager: Annotated[ConnectionManager, Depends(get_connection_manager)],
) -> None:
    await accept_websocket_connection(player, websocket, db, conn_manager)
    await send_initial_state(player, db, conn_manager)
    await db.commit()

    try:
        # Run as a separate task so blocking operations can coexist with polling
        # operations inside this endpoint.
        listening_task = asyncio.create_task(
            listen_for_messages(player, websocket, db, conn_manager)
        )

        await asyncio.gather(listening_task)

    except WebSocketDisconnect:
        await handle_player_disconnect(player, websocket, db, conn_manager)
