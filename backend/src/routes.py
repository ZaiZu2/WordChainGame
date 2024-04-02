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
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

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

    room_out = s.RoomOut(players_no=0, owner_name=player.name, **room.to_dict())
    lobby_state = s.LobbyState(rooms={room.id_: room_out})
    await conn_manager.broadcast_lobby_state(lobby_state)


@router.put('/rooms/{room_id}', status_code=status.HTTP_200_OK)
async def modify_room(
    room_id: int,
    room_in: s.RoomInModify,
    player: Annotated[d.Player, Depends(get_player)],
    db: Annotated[AsyncSession, Depends(get_db)],
    conn_manager: Annotated[ConnectionManager, Depends(get_connection_manager)],
) -> s.RoomState:
    room = await db.scalar(
        select(d.Room).where(d.Room.id_ == room_id).options(joinedload(d.Room.owner))
    )
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Room does not exist'
        )

    room.update(room_in.model_dump())
    db.add(room)
    await db.flush([room])

    room_state = s.RoomState(owner_name=room.owner.name, **room.to_dict())
    await conn_manager.broadcast_room_state(room_state.id_, room_state)

    room_out = s.RoomOut(
        players_no=len(conn_manager.connections[room_id]),
        owner_name=room.owner.name,
        **room.to_dict(),
    )
    lobby_state = s.LobbyState(rooms={room.id_: room_out})
    await conn_manager.broadcast_lobby_state(lobby_state)

    return room_state


@router.post('/rooms/{room_id}/join', status_code=status.HTTP_200_OK)
async def join_room(
    room_id: int,
    player: Annotated[d.Player, Depends(get_player)],
    db: Annotated[AsyncSession, Depends(get_db)],
    conn_manager: Annotated[ConnectionManager, Depends(get_connection_manager)],
) -> s.RoomState:
    room = await db.scalar(
        select(d.Room).where(d.Room.id_ == room_id).options(joinedload(d.Room.owner))
    )
    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Room does not exist'
        )
    if room.status != d.RoomStatusEnum.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Room is not open'
        )
    if len(conn_manager.connections[room_id]) >= room.capacity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Room is full'
        )

    _, old_room_id = conn_manager.find_connection(player.id_)
    await move_player_and_broadcast_message(
        player, old_room_id, room_id, db, conn_manager
    )

    # Broadcast the info about all the players in the room, as the joining player
    # needs that context
    conns = list(conn_manager.connections[room_id])
    room_players = await db.scalars(
        select(d.Player).where(d.Player.id_.in_([conn.player_id for conn in conns]))
    )
    players_out = {
        room_player.name: s.RoomPlayerOut(ready=conn.ready, **room_player.to_dict())
        for room_player, conn in zip(room_players, conns)
    }
    room_state = s.RoomState(
        players=players_out, owner_name=room.owner.name, **room.to_dict()
    )
    await conn_manager.broadcast_room_state(room_state.id_, room_state)

    # Broadcast only the info about the leaving player, as this is all the context other
    # clients need to keep their state up to date
    room_out = s.RoomOut(
        players_no=len(players_out), owner_name=room.owner.name, **room.to_dict()
    )
    lobby_state = s.LobbyState(rooms={room.id_: room_out}, players={player.name: None})
    await conn_manager.broadcast_lobby_state(lobby_state)

    # TODO: Collect chat history and send it to the player
    return room_state.model_dump()


@router.post('/rooms/{room_id}/leave', status_code=status.HTTP_200_OK)
async def leave_room(
    room_id: int,
    player: Annotated[d.Player, Depends(get_player)],
    db: Annotated[AsyncSession, Depends(get_db)],
    conn_manager: Annotated[ConnectionManager, Depends(get_connection_manager)],
) -> s.LobbyState:
    # TODO: Ensure that the player terminated any active game before leaving the room
    # TODO: Ensure that the player is not the owner of the room

    _, old_room_id = conn_manager.find_connection(player.id_, room_id=room_id)
    if old_room_id is None or room_id != old_room_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Player is not in the room'
        )

    await move_player_and_broadcast_message(
        player, old_room_id, d.LOBBY.id_, db, conn_manager
    )

    room = await db.scalar(
        select(d.Room).where(d.Room.id_ == room_id).options(joinedload(d.Room.owner))
    )
    # Ensure the room is not left by the owner in CLOSED status, as it will not be
    # accessible anymore
    if room.owner_id == player.id_ and room.status == d.RoomStatusEnum.CLOSED:
        room.status = d.RoomStatusEnum.OPEN
        db.add(room)
        await db.flush([room])

    # Broadcast only the info about the leaving player, as this is all the context other
    # clients need to keep their state up to date
    room_state = s.RoomState(
        **room.to_dict(),
        owner_name=room.owner.name,
        players={player.name: None},
    )
    await conn_manager.broadcast_room_state(room.id_, room_state)

    # Broadcast the info about all the players in the room, as the joining player
    # needs that context
    room_out = s.RoomOut(
        players_no=len(conn_manager.connections[room_id]),
        owner_name=room.owner.name,
        **room.to_dict(),
    )
    lobby_state = s.LobbyState(
        rooms={room.id_: room_out},
        players={player.name: s.LobbyPlayerOut(**player.to_dict())},
    )
    await conn_manager.broadcast_lobby_state(lobby_state)

    return lobby_state


@router.post('/rooms/{room_id}/status', status_code=status.HTTP_200_OK)
async def toggle_room_status(
    room_id: int,
    player: Annotated[d.Player, Depends(get_player)],
    db: Annotated[AsyncSession, Depends(get_db)],
    conn_manager: Annotated[ConnectionManager, Depends(get_connection_manager)],
):
    """Toggle room status between OPEN and CLOSED."""
    room = await db.scalar(
        select(d.Room).where(d.Room.id_ == room_id).options(joinedload(d.Room.owner))
    )
    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Room not found'
        )
    if room.owner_id != player.id_:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail='Player is not the owner'
        )

    if room.status == d.RoomStatusEnum.CLOSED:
        new_status = d.RoomStatusEnum.OPEN
    elif room.status == d.RoomStatusEnum.OPEN:
        new_status = d.RoomStatusEnum.CLOSED
    else:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, 'Room status must be either OPEN or CLOSED'
        )

    room.status = new_status
    db.add(room)
    await db.flush([room])

    room_state = s.RoomState(
        **room.to_dict(),
        owner_name=room.owner.name,
        players={},
    )
    await conn_manager.broadcast_room_state(room.id_, room_state)

    room_out = s.RoomOut(
        players_no=len(conn_manager.connections[room_id]),
        owner_name=room.owner.name,
        **room.to_dict(),
    )
    lobby_state = s.LobbyState(
        rooms={room.id_: room_out},
        players={},
    )
    await conn_manager.broadcast_lobby_state(lobby_state)


@router.post('/rooms/{room_id}/ready', status_code=status.HTTP_200_OK)
async def toggle_player_readiness(
    room_id: int,
    player: Annotated[d.Player, Depends(get_player)],
    db: Annotated[AsyncSession, Depends(get_db)],
    conn_manager: Annotated[ConnectionManager, Depends(get_connection_manager)],
):
    conn, found_room_id = conn_manager.find_connection(player.id_, room_id=room_id)
    if found_room_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Player is not in the room'
        )

    conn.ready = not conn.ready

    room = await db.scalar(
        select(d.Room).where(d.Room.id_ == room_id).options(joinedload(d.Room.owner))
    )
    room_state = s.RoomState(
        **room.to_dict(),
        owner_name=room.owner.name,
        players={player.name: s.RoomPlayerOut(ready=conn.ready, **player.to_dict())},
    )
    await conn_manager.broadcast_room_state(room.id_, room_state)


@router.get('/stats', status_code=status.HTTP_200_OK)
async def get_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> s.AllTimeStatistics:
    total_games = await db.scalar(
        select(func.count(d.Game.id_)).where(d.Game.status == d.GameStatusEnum.FINISHED)
    )
    # TODO: Calculate the longest chain and the longest game time
    return s.AllTimeStatistics(
        longest_chain=10, longest_game_time=1234, total_games=total_games
    )


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
