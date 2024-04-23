from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

import src.models as d  # d - database
import src.schemas as s  # s - schema
from config import Config
from src.connection_manager import ConnectionManager
from src.dependencies import (
    get_config,
    get_connection_manager,
    get_db,
    get_game_manager,
    get_player,
    get_room,
)
from src.game import GameManager
from src.helpers import (
    TagsEnum,
    loop_turns,
    move_player_and_broadcast_message,
)

router = APIRouter(tags=[TagsEnum.ROOMS])


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

    room = d.Room(**room_in.model_dump())
    room.owner = player
    db.add(room)
    await db.flush([room])
    conn_manager.pool.create_room(room.id_)

    room_out = s.RoomOut(players_no=0, owner_name=player.name, **room.to_dict())
    lobby_state = s.LobbyState(rooms={room.id_: room_out})
    await conn_manager.broadcast_lobby_state(lobby_state)


@router.put('/rooms/{room_id}', status_code=status.HTTP_200_OK)
async def modify_room(
    room_in: s.RoomInModify,
    room: Annotated[d.Room, Depends(get_room)],
    player: Annotated[d.Player, Depends(get_player)],
    db: Annotated[AsyncSession, Depends(get_db)],
    conn_manager: Annotated[ConnectionManager, Depends(get_connection_manager)],
) -> s.RoomState:
    room.update(room_in.model_dump())
    db.add(room)
    await db.flush([room])

    room_state = s.RoomState(owner_name=room.owner.name, **room.to_dict())
    await conn_manager.broadcast_room_state(room_state.id_, room_state)

    room_conns = conn_manager.pool.get_room_conns(room.id_)
    room_out = s.RoomOut(
        players_no=len(room_conns),
        owner_name=room.owner.name,
        **room.to_dict(),
    )
    lobby_state = s.LobbyState(rooms={room.id_: room_out})
    await conn_manager.broadcast_lobby_state(lobby_state)

    return room_state


@router.post('/rooms/{room_id}/join', status_code=status.HTTP_200_OK)
async def join_room(
    room: Annotated[d.Room, Depends(get_room)],
    player: Annotated[d.Player, Depends(get_player)],
    db: Annotated[AsyncSession, Depends(get_db)],
    conn_manager: Annotated[ConnectionManager, Depends(get_connection_manager)],
) -> s.RoomState:
    conn = conn_manager.pool.get_conn(player.id_)
    old_room_id = conn_manager.pool.get_room_id(player.id_)

    if room.id_ == old_room_id:
        return s.RoomState(owner_name=room.owner.name, **room.to_dict())
    if room.status != d.RoomStatusEnum.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Room is not open'
        )
    if len(conn_manager.pool.get_room_conns(room.id_)) >= room.capacity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Room is full'
        )

    await move_player_and_broadcast_message(
        player, old_room_id, room.id_, db, conn_manager
    )
    if player.id_ == room.owner_id:
        conn.ready = True

    # Broadcast the info about all the players in the room, as the joining player
    # needs that context
    conns = list(conn_manager.pool.get_room_conns(room.id_))
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
    return room_state


@router.post('/rooms/{room_id}/leave', status_code=status.HTTP_200_OK)
async def leave_room(
    room: Annotated[d.Room, Depends(get_room)],
    player: Annotated[d.Player, Depends(get_player)],
    db: Annotated[AsyncSession, Depends(get_db)],
    conn_manager: Annotated[ConnectionManager, Depends(get_connection_manager)],
) -> s.LobbyState:
    # TODO: Ensure that the player terminated any active game before leaving the room
    # TODO: Ensure that the player is not the owner of the room
    old_room_id = conn_manager.pool.get_room_id(player.id_)
    if old_room_id is None or room.id_ != old_room_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Player is not in the room'
        )

    await move_player_and_broadcast_message(
        player, old_room_id, d.LOBBY.id_, db, conn_manager
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
        players_no=len(conn_manager.pool.get_room_conns(room.id_)),
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
    room: Annotated[d.Room, Depends(get_room)],
    player: Annotated[d.Player, Depends(get_player)],
    db: Annotated[AsyncSession, Depends(get_db)],
    conn_manager: Annotated[ConnectionManager, Depends(get_connection_manager)],
):
    """Toggle room status between OPEN and CLOSED."""
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
        players_no=len(conn_manager.pool.get_room_conns(room.id_)),
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
    room: Annotated[d.Room, Depends(get_room)],
    player: Annotated[d.Player, Depends(get_player)],
    db: Annotated[AsyncSession, Depends(get_db)],
    conn_manager: Annotated[ConnectionManager, Depends(get_connection_manager)],
):
    conn = conn_manager.pool.get_conn(player.id_)
    found_room_id = conn_manager.pool.get_room_id(player.id_)
    if found_room_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Player is not in the room'
        )

    conn.ready = not conn.ready

    room_state = s.RoomState(
        **room.to_dict(),
        owner_name=room.owner.name,
        players={player.name: s.RoomPlayerOut(ready=conn.ready, **player.to_dict())},
    )
    await conn_manager.broadcast_room_state(room.id_, room_state)


@router.post('/rooms/{room_id}/start', status_code=status.HTTP_201_CREATED)
async def start_game(
    room: Annotated[d.Room, Depends(get_room)],
    player: Annotated[d.Player, Depends(get_player)],
    db: Annotated[AsyncSession, Depends(get_db)],
    conn_manager: Annotated[ConnectionManager, Depends(get_connection_manager)],
    game_manager: Annotated[GameManager, Depends(get_game_manager)],
    config: Annotated[Config, Depends(get_config)],
) -> None:
    if room.owner_id != player.id_:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Player is not the owner'
        )

    found_room_id = conn_manager.pool.get_room_id(player.id_)
    if found_room_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Player is not in the room'
        )
    if not all(conn.ready for conn in conn_manager.pool.get_room_conns(room.id_)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Not all players are ready'
        )

    room.status = d.RoomStatusEnum.IN_PROGRESS
    # Load all players from the db to create a many-to-many relationship with the game placeholder
    players = (
        await db.scalars(
            select(d.Player).where(
                d.Player.id_.in_(
                    [
                        conn.player_id
                        for conn in conn_manager.pool.get_room_conns(room.id_)
                    ]
                )
            )
        )
    ).fetchall()

    # Create game placeholder in the database to assign the ID
    game_db = d.Game(
        status=d.GameStatusEnum.IN_PROGRESS,
        rules=room.rules,
        room_id=room.id_,
        # TODO: Figure out why instantiating `d.Game` with `players` issues multiple
        # INSERT statements, violating the unique constraint
        # players=players,
    )
    db.add_all([game_db, room])
    await db.flush([game_db, room])

    # HACK: Insert the many-to-many relationship manually
    await db.execute(
        insert(d.players_games_table).values(
            [{'game_id': game_db.id_, 'player_id': player.id_} for player in players]
        )
    )
    await db.refresh(game_db, attribute_names=['players'])

    # Store the game in memory during it's progress
    game = game_manager.create(game_db)

    # Update everyone with the status change of the room
    room_state = s.RoomState(**room.to_dict(), owner_name=room.owner.name)
    await conn_manager.broadcast_room_state(room.id_, room_state)

    room_out = s.RoomOut(
        players_no=len(conn_manager.pool.get_room_conns(room.id_)),
        owner_name=room.owner.name,
        **room.to_dict(),
    )
    lobby_state = s.LobbyState(rooms={room.id_: room_out})
    await conn_manager.broadcast_lobby_state(lobby_state)

    # Broadcast the initial game state to all players
    start_game_state = game.start()
    await conn_manager.broadcast_game_state(room.id_, start_game_state)

    await loop_turns(game, room.id_, conn_manager, config)
