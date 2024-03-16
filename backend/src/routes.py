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
    broadcast_full_lobby_state,
    handle_player_disconnect,
    listen_for_messages,
    move_player_and_broadcast_message,
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
    conn_manager.connections[room.id_] = set()

    room_out = s.RoomOut(players_no=0, **room.to_dict())
    lobby_state = s.LobbyState(rooms={room.id_: room_out})
    await conn_manager.broadcast_lobby_state(lobby_state)


@router.post('/rooms/{room_id}/join', status_code=status.HTTP_200_OK)
async def join_room(
    room_id: int,
    player: Annotated[d.Player, Depends(get_player)],
    db: Annotated[AsyncSession, Depends(get_db)],
    conn_manager: Annotated[ConnectionManager, Depends(get_connection_manager)],
) -> s.RoomState:
    room = await db.scalar(select(d.Room).where(d.Room.id_ == room_id))
    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Room does not exist'
        )
    if room.status != d.RoomStatusEnum.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Room is not accessible'
        )
    if len(conn_manager.connections[room_id]) >= room.capacity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Room is full'
        )

    _, old_room_id = conn_manager.find_connection(player.id_)
    await move_player_and_broadcast_message(player, old_room_id, room_id, db, conn_manager)

    # Broadcast the info about all the players in the room, as the joining player
    # needs that context
    player_ids = [conn.player_id for conn in conn_manager.connections[room_id]]
    room_players = await db.scalars(
        select(d.Player).where(d.Player.id_.in_(player_ids))
    )
    players_out = {
        room_player.name: s.PlayerOut(**room_player.to_dict())
        for room_player in room_players
    }
    room_state = s.RoomState(players=players_out, **room.to_dict())
    await conn_manager.broadcast_room_state(room.id_, room_state)

    # Broadcast only the info about the leaving player, as this is all the context other
    # clients need to keep their state up to date
    room_out = s.RoomOut(players_no=len(players_out), **room.to_dict())
    lobby_state = s.LobbyState(rooms={room.id_: room_out}, players={player.name: None})
    await conn_manager.broadcast_lobby_state(lobby_state)

    # TODO: Collect chat history and send it to the player
    return room_state


@router.post('/rooms/{room_id}/leave', status_code=status.HTTP_200_OK)
async def leave_room(
    room_id: int,
    player: Annotated[d.Player, Depends(get_player)],
    db: Annotated[AsyncSession, Depends(get_db)],
    conn_manager: Annotated[ConnectionManager, Depends(get_connection_manager)],
):
    # TODO: Ensure that the player terminated any active game before leaving the room
    # TODO: Ensure that the player is not the owner of the room

    room = await db.scalar(select(d.Room).where(d.Room.id_ == room_id))
    _, old_room_id = conn_manager.find_connection(player.id_)
    if room is None or room_id != old_room_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail='Player is not in the room'
        )

    move_player_and_broadcast_message(player, old_room_id, room_id, db, conn_manager)

    # Broadcast only the info about the leaving player, as this is all the context other
    # clients need to keep their state up to date
    room_state = s.RoomState(**room.to_dict(), players={player.name: None})
    await conn_manager.broadcast_room_state(room.id_, room_state)

    # Broadcast the info about all the players in the room, as the joining player
    # needs that context
    room_out = s.RoomOut(
        players_no=len(conn_manager.connections[room_id]), **room.to_dict()
    )
    lobby_state = s.LobbyState(
        rooms={room.id_: room_out},
        players={player.name: s.PlayerOut(**player.to_dict())},
    )
    await conn_manager.broadcast_lobby_state(lobby_state)


@router.websocket('/connect')
async def connect(
    websocket: WebSocket,
    player: Annotated[d.Player, Depends(get_player)],
    db: Annotated[AsyncSession, Depends(get_db)],
    conn_manager: Annotated[ConnectionManager, Depends(get_connection_manager)],
) -> None:
    await accept_websocket_connection(player, websocket, db, conn_manager)
    await broadcast_full_lobby_state(db, conn_manager)
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
