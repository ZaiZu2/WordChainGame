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

import src.database as d  # d - database
import src.schemas as s  # s - schema
from config import Config, get_config
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
    player: Annotated[d.Player, Depends(get_player)],
) -> s.Player:
    return player


@router.post('/players', status_code=status.HTTP_201_CREATED)
async def create_player(
    name: Annotated[str, Body(embed=True, max_length=10)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> s.Player:
    if await db.scalar(select(d.Player).where(d.Player.name == name)):
        raise HTTPException(
            status_code=409, detail=[f'Player with name {name} already exists']
        )

    player = d.Player(name=name)
    db.add(player)
    await db.flush()
    await db.refresh(player)

    return s.Player.model_validate(player)


@router.post('/players/login', status_code=status.HTTP_200_OK)
async def login_player(
    id_: Annotated[UUID, Body(embed=True, alias='id')],
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> s.Player:
    player = await db.scalar(select(d.Player).where(d.Player.id_ == id_))
    if not player:
        raise HTTPException(status.HTTP_403_FORBIDDEN, 'Player not found')

    await set_auth_cookie(player.id_, response)
    return s.Player.model_validate(player)


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
) -> s.Player:
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
    game_manager: Annotated[GameManager, Depends(get_game_manager)],
    config: Annotated[Config, Depends(get_config)],
) -> None:
    await accept_websocket_connection(player, websocket, db, conn_manager)
    await broadcast_full_lobby_state(
        db, conn_manager
    )  # TODO: Send instead of broadcast
    await db.commit()

    try:
        # Run as a separate task so blocking operations can coexist with polling
        # operations inside this endpoint.
        listening_task = asyncio.create_task(
            listen_for_messages(player, websocket, db, conn_manager, game_manager)
        )

        await asyncio.gather(listening_task)

    except WebSocketDisconnect:
        await handle_player_disconnect(player, db, conn_manager)
