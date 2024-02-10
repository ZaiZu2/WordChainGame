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

import src.models as d  # d - database
import src.schemas as s  # s - schema
from src.connection_manager import ConnectionManager
from src.dependencies import (
    get_connection_manager,
    get_db,
    get_player,
    set_auth_cookie,
)
from src.fastapi_utils import TagsEnum, persist_and_save_message
from src.models import get_root_user

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
    # Room with id 1 is the lobby
    rooms = await db.scalars(select(d.Room).where(d.Room.id_ != 1))
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


@router.websocket('/connect')
async def connect(
    websocket: WebSocket,
    player: Annotated[d.Player, Depends(get_player)],
    db: Annotated[AsyncSession, Depends(get_db)],
    conn_manager: Annotated[ConnectionManager, Depends(get_connection_manager)],
) -> None:
    root_player = await get_root_user(db)

    conn_manager.connect(player.id_, player.room_id, websocket)
    await websocket.accept()
    # TODO: When websockets connects, it should send the initial package of data
    # if room_id == 0 (lobby):
    # send the list of available rooms and 10 last messages in the chat
    # if room_id != 0 (game room):
    # send all messages in the chat + game_state
    message = d.Message(
        content=f'{player.name} joined the room',
        room_id=player.room_id,
        player=root_player,
    )
    await persist_and_save_message(message, db, conn_manager)

    try:
        while True:
            # TODO: Make a wrapper which deserializes the websocket message when it arrives
            websocket_message_dict = await websocket.receive_json()
            websocket_message = s.WebSocketMessage(**websocket_message_dict)

            match websocket_message.type:
                # TODO: Make a wrapper which handles CHAT type websocket messages
                case s.WebSocketMessageType.CHAT:
                    message = d.Message(
                        content=websocket_message.payload.content,
                        room_id=websocket_message.payload.room_id,
                        player=player,
                    )
                    await persist_and_save_message(message, db, conn_manager)
                case s.WebSocketMessageType.GAME_STATE:
                    pass
    except WebSocketDisconnect:
        await db.refresh(player)
        conn_manager.disconnect(player.id_, player.room_id, websocket)
        message = d.Message(
            content=f'{player.name} left the room',
            room_id=player.room_id,
            player=root_player,
        )
        await persist_and_save_message(message, db, conn_manager)
