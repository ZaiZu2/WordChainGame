import asyncio
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

import src.schemas.database as db
import src.schemas.domain as d
import src.schemas.validation as v
from src.api.utils import cast_v2d_rules
from src.connection_manager import ConnectionManager
from src.dependencies import (
    get_connection_manager,
    get_db_session,
    get_game_manager,
    get_player,
    get_room,
)
from src.game.game import GameManager
from src.helpers import (
    TagsEnum,
    broadcast_single_room_state,
    get_current_stats,
    move_player_and_broadcast_message,
    run_game,
    save_and_broadcast_message,
)

router = APIRouter(tags=[TagsEnum.ROOMS])


@router.post('/rooms', status_code=status.HTTP_201_CREATED)
async def create_room(
    room_in: v.RoomIn,
    player: Annotated[d.Player, Depends(get_player)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    conn_manager: Annotated[ConnectionManager, Depends(get_connection_manager)],
) -> v.RoomOut:
    if await db_session.scalar(select(db.Room).where(db.Room.name == room_in.name)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'Game room with name {room_in.name} already exists',
        )

    room_db = db.Room(name=room_in.name)
    db_session.add(room_db)
    await db_session.flush([room_db])

    room = d.Room(
        id_=room_db.id_,
        name=room_db.name,
        capacity=room_in.capacity,
        created_on=room_db.created_on,
        owner=player,
        rules=cast_v2d_rules(room_in.rules),
    )  # fmt: off
    conn_manager.pool.create_room(room)

    room_out = v.RoomOut(players_no=0, owner_name=player.name, **room.to_dict())
    lobby_state = v.LobbyState(
        rooms={room.id_: room_out}, stats=get_current_stats(conn_manager)
    )
    await conn_manager.broadcast_lobby_state(lobby_state)
    return room_out


@router.put('/rooms/{room_id}', status_code=status.HTTP_200_OK)
async def modify_room(
    room_in_modify: v.RoomInModify,
    room: Annotated[d.Room, Depends(get_room)],
    player: Annotated[d.Player, Depends(get_player)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    conn_manager: Annotated[ConnectionManager, Depends(get_connection_manager)],
) -> v.RoomOut:
    if room_in_modify.capacity < len(room.players):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            'Room capacity cannot be set below the current number of players',
        )

    room.update(**room_in_modify.model_dump())

    room_players = conn_manager.pool.get_room_players(room.id_)
    for room_player in room_players:
        room_player.ready = False

    message_db = db.Message(
        content='game settings have been changed',
        room_id=room.id_,
        player_id=d.ROOT.id_,
    )
    await save_and_broadcast_message(message_db, db_session, conn_manager)

    await broadcast_single_room_state(room, conn_manager)
    return v.RoomOut(
        players_no=len(room_players),
        owner_name=room.owner.name,
        **room.to_dict(),
    )


@router.post('/rooms/{room_id}/join', status_code=status.HTTP_200_OK)
async def join_room(
    room: Annotated[d.Room, Depends(get_room)],
    player: Annotated[d.Player, Depends(get_player)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    conn_manager: Annotated[ConnectionManager, Depends(get_connection_manager)],
) -> v.RoomState:
    old_room_id = conn_manager.pool.get_room(player_id=player.id_).id_

    if room.id_ == old_room_id:
        return v.RoomState(owner_name=room.owner.name, **room.to_dict())
    if room.status != d.RoomStatusEnum.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Room is not open'
        )
    if len(room.players) >= room.capacity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Room is full'
        )

    await move_player_and_broadcast_message(
        player, old_room_id, room.id_, db_session, conn_manager
    )

    # Broadcast the info about all the players in the room, as the joining player
    # needs that context
    room_players = conn_manager.pool.get_room_players(room.id_)
    players_out = {
        player.name: v.RoomPlayerOut.model_validate(player) for player in room_players
    }
    room_state = v.RoomState(
        players=players_out, owner_name=room.owner.name, **room.to_dict()
    )
    await conn_manager.broadcast_room_state(room_state.id_, room_state)

    # Broadcast only the info about the leaving player, as this is all the context other
    # clients need to keep their state up to date
    room_out = v.RoomOut(
        players_no=len(players_out), owner_name=room.owner.name, **room.to_dict()
    )
    lobby_state = v.LobbyState(
        rooms={room.id_: room_out},
        players={player.name: None},
        stats=get_current_stats(conn_manager),
    )
    await conn_manager.broadcast_lobby_state(lobby_state)

    # TODO: Collect chat history and send it to the player
    return room_state


@router.post('/rooms/{room_id}/leave', status_code=status.HTTP_200_OK)
async def leave_room(
    room: Annotated[d.Room, Depends(get_room)],
    player: Annotated[d.Player, Depends(get_player)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    conn_manager: Annotated[ConnectionManager, Depends(get_connection_manager)],
) -> v.LobbyState:
    # TODO: Ensure that the player terminated any active game before leaving the room
    # TODO: Ensure that the player is not the owner of the room
    old_room_id = conn_manager.pool.get_room(player_id=player.id_).id_
    if old_room_id is None or room.id_ != old_room_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Player is not in the room'
        )

    await move_player_and_broadcast_message(
        player, old_room_id, d.LOBBY.id_, db_session, conn_manager
    )

    # Ensure the room is not left by the owner in CLOSED status, as it will not be
    # accessible anymore
    if room.owner.id_ == player.id_ and room.status == d.RoomStatusEnum.CLOSED:
        room.status = d.RoomStatusEnum.OPEN

    # Broadcast only the info about the leaving player, as this is all the context other
    # clients need to keep their state up to date
    room_state = v.RoomState(
        **room.to_dict(),
        owner_name=room.owner.name,
        players={player.name: None},
    )
    await conn_manager.broadcast_room_state(room.id_, room_state)

    # Broadcast the info about all the players in the lobby, as the joining player
    # needs that context
    room_out = v.RoomOut(
        players_no=len(conn_manager.pool.get_room_players(room.id_)),
        owner_name=room.owner.name,
        **room.to_dict(),
    )
    lobby_state = v.LobbyState(
        rooms={room.id_: room_out},
        players={player.name: v.LobbyPlayerOut(**player.to_dict())},
        stats=get_current_stats(conn_manager),
    )
    await conn_manager.broadcast_lobby_state(lobby_state)

    return lobby_state


@router.post('/rooms/{room_id}/status', status_code=status.HTTP_200_OK)
async def toggle_room_status(
    room: Annotated[d.Room, Depends(get_room)],
    player: Annotated[d.Player, Depends(get_player)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    conn_manager: Annotated[ConnectionManager, Depends(get_connection_manager)],
):
    """Toggle room status between OPEN and CLOSED."""
    if room.owner.id_ != player.id_:
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

    room_state = v.RoomState(**room.to_dict(), owner_name=room.owner.name, players={})
    await conn_manager.broadcast_room_state(room.id_, room_state)

    room_out = v.RoomOut(
        players_no=len(conn_manager.pool.get_room_players(room.id_)),
        owner_name=room.owner.name,
        **room.to_dict(),
    )
    lobby_state = v.LobbyState(
        rooms={room.id_: room_out}, players={}, stats=get_current_stats(conn_manager)
    )
    await conn_manager.broadcast_lobby_state(lobby_state)


@router.post('/rooms/{room_id}/ready', status_code=status.HTTP_200_OK)
async def toggle_player_readiness(
    room: Annotated[d.Room, Depends(get_room)],
    player: Annotated[d.Player, Depends(get_player)],
    conn_manager: Annotated[ConnectionManager, Depends(get_connection_manager)],
) -> None:
    player.ready = not player.ready

    room_state = v.RoomState(
        **room.to_dict(),
        owner_name=room.owner.name,
        players={player.name: v.RoomPlayerOut.model_validate(player)},
    )
    await conn_manager.broadcast_room_state(room.id_, room_state)


@router.post('/rooms/{room_id}/return', status_code=status.HTTP_200_OK)
async def return_from_game(
    room: Annotated[d.Room, Depends(get_room)],
    player: Annotated[d.Player, Depends(get_player)],
    conn_manager: Annotated[ConnectionManager, Depends(get_connection_manager)],
) -> None:
    """Inform the room that the player returned to the room from the previous game."""
    player.in_game = False

    room_state = v.RoomState(
        **room.to_dict(),
        owner_name=room.owner.name,
        players={player.name: v.RoomPlayerOut.model_validate(player)},
    )
    await conn_manager.broadcast_room_state(room.id_, room_state)


# TODO: Probably implement UUID as a player `password` and normal INT PK as
# identifier which can be shared with the client. This is getting really messy.
@router.post(
    '/rooms/{room_id}/players/{player_name}/kick', status_code=status.HTTP_200_OK
)
async def kick_player(
    player_name: str,
    room: Annotated[d.Room, Depends(get_room)],
    player: Annotated[d.Player, Depends(get_player)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    conn_manager: Annotated[ConnectionManager, Depends(get_connection_manager)],
) -> None:
    if room.owner.id_ != player.id_:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail='Player is not the owner'
        )

    player_to_kick = next(
        (
            room_player
            for room_player in room.players.values()
            if room_player.name == player_name
        ),
        None,
    )
    if player_to_kick is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Player to kick is not in the room',
        )

    await conn_manager.send_action(v.Action(action='KICK_PLAYER'), player_to_kick.id_)
    await move_player_and_broadcast_message(
        player_to_kick,
        room.id_,
        d.LOBBY.id_,
        db_session,
        conn_manager,
        leave_message=f'{player_to_kick.name} got kicked from the room',
    )

    # Broadcast only the info about the leaving player, as this is all the context other
    # clients need to keep their state up to date
    room_state = v.RoomState(
        **room.to_dict(),
        owner_name=room.owner.name,
        players={player_to_kick.name: None},
    )
    await conn_manager.broadcast_room_state(room.id_, room_state)

    # Broadcast the info about all the players in the room, as the joining player
    # needs that context
    room_out = v.RoomOut(
        players_no=len(conn_manager.pool.get_room_players(room.id_)),
        owner_name=room.owner.name,
        **room.to_dict(),
    )
    lobby_state = v.LobbyState(
        rooms={room.id_: room_out},
        players={player.name: v.LobbyPlayerOut(**player_to_kick.to_dict())},
        stats=get_current_stats(conn_manager),
    )
    await conn_manager.broadcast_lobby_state(lobby_state)


@router.post('/rooms/{room_id}/start', status_code=status.HTTP_201_CREATED)
async def start_game(
    room: Annotated[d.Room, Depends(get_room)],
    player: Annotated[d.Player, Depends(get_player)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    conn_manager: Annotated[ConnectionManager, Depends(get_connection_manager)],
    game_manager: Annotated[GameManager, Depends(get_game_manager)],
) -> None:
    player.ready = True

    if room.owner.id_ != player.id_:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Player is not the owner'
        )
    if room is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Player is not in the room'
        )
    if not all(player.ready for player in conn_manager.pool.get_room_players(room.id_)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Not all players are ready'
        )

    room.status = d.RoomStatusEnum.IN_PROGRESS
    # Create game placeholder in the database to assign the ID
    game_db = db.Game(
        status=db.GameStatusEnum.STARTED,
        rules=room.rules.to_dict(),
        room_id=room.id_,
    )
    db_session.add(game_db)
    await db_session.flush([game_db])
    await db_session.execute(
        insert(db.players_games_table).values(
            [
                {'game_id': game_db.id_, 'player_id': room_player.id_}
                for room_player in room.players.values()
            ]
        )
    )
    await broadcast_single_room_state(room, conn_manager)

    game = game_manager.create(game_db.id_, room.rules, room.players.values())
    asyncio.create_task(run_game(game, room, conn_manager))

    players_out = {}
    for player in room.players.values():
        player.ready = False
        player.in_game = True
        players_out[player.name] = v.RoomPlayerOut.model_validate(player)

    room_state = v.RoomState(
        players=players_out, owner_name=room.owner.name, **room.to_dict()
    )
    await conn_manager.broadcast_room_state(room_state.id_, room_state)
