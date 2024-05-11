from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from config import LOGGING_CONFIG
from src.api import main, rooms
from src.database import create_root_objects, recreate_database
from src.error_handlers import request_validation_handler
from src.helpers import tags_metadata


@asynccontextmanager
async def lifespan(app: FastAPI):
    # HACK: Temporary DB recreation logic for repeatable development environment
    # Must be removed for a production environment
    await recreate_database()
    await create_root_objects()
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

    app.include_router(main.router)
    app.include_router(rooms.router)

    app.add_exception_handler(RequestValidationError, request_validation_handler)

    Path('./logs').mkdir(exist_ok=True)

    return app


app = create_app()
if __name__ == '__main__':
    uvicorn.run(app, log_config=LOGGING_CONFIG)
