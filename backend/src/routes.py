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


@router.websocket('connect')
async def connect(
    websocket: WebSocket,
    player: Annotated[d.Player, Depends(get_player)],
    db: Annotated[AsyncSession, Depends(get_db)],
    conn_manager: Annotated[ConnectionManager, Depends(get_connection_manager)],
) -> None:
    #### INITIAL CONNECTION PHASE ####
    await websocket.accept()
    await conn_manager.connect(player.id_, player.room_id, websocket)
    # TODO: When websockets connects, it should send the initial package of data
    # if room_id == 0 (lobby):
    # send the list of available rooms and 10 last messages in the chat
    # if room_id != 0 (game room):
    # send all messages in the chat + game_state
    await conn_manager.broadcast_chat_message(
        player.room_id, f'Player {player.name} joined the room'
    )

    #### LISTENING PHASE ####
    try:
        while True:
            # TODO: Make a wrapper which deserializes the websocket message when it arrives
            websocket_message_json = await websocket.receive_json()
            websocket_message = s.WebSocketMessage.model_validate(
                websocket_message_json
            )

            match websocket_message.type:
                # TODO: Make a wrapper which handles CHAT type websocket messages
                case s.WebSocketMessageType.CHAT:
                    await conn_manager.broadcast_chat_message(
                        websocket_message.payload,
                        player_name=player.name,
                        room_id=player.room_id,
                    )

                    # TODO: Persistence switched off for now
                    # message = d.Message(
                    #     content=message_string, room_id=player.room_id, player=player
                    # )
                    # db.add(message)
                    # await db.commit()
                case s.WebSocketMessageType.GAME_STATE:
                    pass

    # TODO: Make a wrapper which catches the websocket disconnect exception
    except WebSocketDisconnect:
        await conn_manager.disconnect(player.id_, player.room_id, websocket)
        await conn_manager.broadcast_chat_message(
            player.room_id, f'Player {player.name} left the room'
        )
