from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from config import LOGGING_CONFIG, get_config
from src.api import main, rooms
from src.database import create_root_objects, recreate_database
from src.dependencies import get_connection_manager
from src.helpers import expire_inactive_rooms, schedule_recurring_task, tags_metadata
from src.misc import request_validation_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # HACK: Temporary DB recreation logic for repeatable development environment
    # Must be removed for a production environment
    await recreate_database()
    await create_root_objects()

    # Schedule recurring tasks
    started_on = datetime.utcnow().replace(second=0, microsecond=0)
    schedule_recurring_task(
        started_on,
        interval=get_config().ROOM_DELETION_INTERVAL,
        coro_func=expire_inactive_rooms,
        kwargs={'conn_manager': get_connection_manager()},
    )
    yield


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan, openapi_tags=tags_metadata)

    origins = [
        'http://localhost:3000',
        'http://127.0.0.1:3000',
        'https://localhost:3000',
        'https://127.0.0.1:3000',
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    app.include_router(main.router, prefix='/api')
    app.include_router(rooms.router, prefix='/api')

    app.add_exception_handler(RequestValidationError, request_validation_handler)

    Path('./logs').mkdir(exist_ok=True)

    return app


app = create_app()
if __name__ == '__main__':
    uvicorn.run(app, log_config=LOGGING_CONFIG)
