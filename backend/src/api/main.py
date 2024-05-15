import asyncio
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

import src.schemas.database as db
import src.schemas.domain as d
import src.schemas.validation as v
from src.connection_manager import ConnectionManager
from src.dependencies import (
    get_connection_manager,
    get_db_session,
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
) -> v.Player:
    return v.Player.model_validate(player)


@router.post('/players', status_code=status.HTTP_201_CREATED)
async def create_player(
    name: Annotated[str, Body(embed=True, max_length=10)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> v.Player:
    if await db_session.scalar(select(db.Player).where(db.Player.name == name)):
        raise HTTPException(
            status_code=409, detail=[f'Player with name {name} already exists']
        )

    player_db = db.Player(name=name)
    db_session.add(player_db)
    await db_session.flush()
    await db_session.refresh(player_db)

    return v.Player(**player_db.to_dict())


@router.post('/players/login', status_code=status.HTTP_200_OK)
async def login_player(
    id_: Annotated[UUID, Body(embed=True, alias='id')],
    response: Response,
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> v.Player:
    player_db = await db_session.scalar(select(db.Player).where(db.Player.id_ == id_))
    if not player_db:
        raise HTTPException(status.HTTP_403_FORBIDDEN, 'Player not found')

    await set_auth_cookie(player_db.id_, response)
    return v.Player(**player_db.to_dict())


@router.post('/players/logout', status_code=status.HTTP_200_OK)
async def logout_player(
    response: Response, player: Annotated[d.Player, Depends(get_player)]
) -> None:
    await set_auth_cookie('', response)


# Feature currently disabled
@router.put('/players', status_code=status.HTTP_200_OK)
async def update_player_name(
    name: Annotated[str, Body(embed=True)],
    player: Annotated[d.Player, Depends(get_player)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> v.Player:
    raise NotImplementedError('disabled')
    if db_session.scalar(select(db.Player).where(db.Player.name == name)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=[f'Player with name {name} already exists'],
        )

    player.name = name
    db.add(player)
    await db.flush()
    await db.refresh(player)
    return v.Player.model_validate(player)


@router.get('/stats', status_code=status.HTTP_200_OK)
async def get_stats(
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> v.AllTimeStatistics:
    total_games = await db_session.scalar(
        select(func.count(db.Game.id_)).where(
            db.Game.status == d.GameStatusEnum.FINISHED
        )
    )
    # TODO: Calculate the longest chain and the longest game time
    return v.AllTimeStatistics(
        longest_chain=10, longest_game_time=1234, total_games=total_games
    )


@router.websocket('/connect')
async def connect(
    websocket: WebSocket,
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    conn_manager: Annotated[ConnectionManager, Depends(get_connection_manager)],
    game_manager: Annotated[GameManager, Depends(get_game_manager)],
    player_id: Annotated[UUID | Literal[''] | None, Cookie()] = None,
) -> None:
    if player_id is None or player_id == '':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Player is not authenticated',
        )
    player_db = await db_session.scalar(
        select(db.Player).where(db.Player.id_ == player_id)
    )
    player = d.Player(**player_db.to_dict(), room=d.LOBBY, websocket=websocket)
    await accept_websocket_connection(player, websocket, db_session, conn_manager)
    await broadcast_full_lobby_state(conn_manager)

    try:
        # Run as a separate task so blocking operations can coexist with future polling
        # operations inside this endpoint.
        listening_task = asyncio.create_task(
            listen_for_messages(player, db_session, conn_manager, game_manager)
        )
        await asyncio.gather(listening_task)

    except WebSocketDisconnect:
        await handle_player_disconnect(player, db_session, conn_manager)
