import asyncio
from dataclasses import asdict
from typing import Annotated, Literal
from uuid import UUID

from fastapi import (
    APIRouter,
    Body,
    Cookie,
    Depends,
    HTTPException,
    Response,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

import src.database as d  # d - database
import src.schemas.domain as m  # m - domain
import src.schemas.validation as v  # v - validation
from src.connection_manager import ConnectionManager
from src.dependencies import (
    get_connection_manager,
    get_db,
    get_game_manager,
    get_player,
    set_auth_cookie,
)
from src.game.game import GameManager
from src.helpers import (
    TagsEnum,
    accept_websocket_connection,
    broadcast_full_lobby_state,
    handle_player_disconnect,
    listen_for_messages,
)

router = APIRouter(tags=[TagsEnum.MAIN])


@router.get('/players/me', status_code=status.HTTP_200_OK)
async def get_client_player(
    player: Annotated[m.Player, Depends(get_player)],
) -> v.Player:
    return v.Player(**asdict(player))


@router.post('/players', status_code=status.HTTP_201_CREATED)
async def create_player(
    name: Annotated[str, Body(embed=True, max_length=10)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> v.Player:
    if await db.scalar(select(d.Player).where(d.Player.name == name)):
        raise HTTPException(
            status_code=409, detail=[f'Player with name {name} already exists']
        )

    player_db = d.Player(name=name)
    db.add(player_db)
    await db.flush()
    await db.refresh(player_db)

    return v.Player(**player_db.to_dict())


@router.post('/players/login', status_code=status.HTTP_200_OK)
async def login_player(
    id_: Annotated[UUID, Body(embed=True, alias='id')],
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> v.Player:
    player_db = await db.scalar(select(d.Player).where(d.Player.id_ == id_))
    if not player_db:
        raise HTTPException(status.HTTP_403_FORBIDDEN, 'Player not found')

    await set_auth_cookie(player_db.id_, response)
    return v.Player(**player_db.to_dict())


@router.post('/players/logout', status_code=status.HTTP_200_OK)
async def logout_player(
    response: Response, player: Annotated[m.Player, Depends(get_player)]
) -> None:
    await set_auth_cookie('', response)


# Feature currently disabled
@router.put('/players', status_code=status.HTTP_200_OK)
async def update_player_name(
    name: Annotated[str, Body(embed=True)],
    player: Annotated[m.Player, Depends(get_player)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> v.Player:
    raise NotImplementedError('disabled')
    if db.scalar(select(d.Player).where(d.Player.name == name)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=[f'Player with name {name} already exists'],
        )

    player.name = name
    db.add(player)
    await db.flush()
    await db.refresh(player)
    return v.Player(**asdict(player))


@router.get('/stats', status_code=status.HTTP_200_OK)
async def get_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> v.AllTimeStatistics:
    total_games = await db.scalar(
        select(func.count(d.Game.id_)).where(d.Game.status == m.GameStatusEnum.FINISHED)
    )
    # TODO: Calculate the longest chain and the longest game time
    return v.AllTimeStatistics(
        longest_chain=10, longest_game_time=1234, total_games=total_games
    )


@router.websocket('/connect')
async def connect(
    websocket: WebSocket,
    db: Annotated[AsyncSession, Depends(get_db)],
    conn_manager: Annotated[ConnectionManager, Depends(get_connection_manager)],
    game_manager: Annotated[GameManager, Depends(get_game_manager)],
    player_id: Annotated[UUID | Literal[''] | None, Cookie()] = None,
) -> None:
    if player_id is None or player_id == '':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Player is not authenticated',
        )
    player_db = await db.scalar(select(d.Player).where(d.Player.id_ == player_id))
    player = m.Player(**player_db.to_dict(), room=m.LOBBY, websocket=websocket)

    await accept_websocket_connection(player, websocket, db, conn_manager)
    await broadcast_full_lobby_state(db, conn_manager)
    await db.commit()

    try:
        # Run as a separate task so blocking operations can coexist with future polling
        # operations inside this endpoint.
        listening_task = asyncio.create_task(
            listen_for_messages(player, db, conn_manager, game_manager)
        )
        await asyncio.gather(listening_task)

    except WebSocketDisconnect:
        await handle_player_disconnect(player, db, conn_manager)
