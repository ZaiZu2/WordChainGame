from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

import src.routes as routes
from config import LOGGING_CONFIG
from src.error_handlers import request_validation_handler
from src.helpers import tags_metadata
from src.models import create_root_objects, recreate_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    await recreate_database()
    await create_root_objects()
    yield


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan, openapi_tags=tags_metadata)

    origins = ['http://localhost:3000']
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    app.include_router(routes.router)

    app.add_exception_handler(RequestValidationError, request_validation_handler)

    Path('./logs').mkdir(exist_ok=True)

    return app


app = create_app()
if __name__ == '__main__':
    uvicorn.run(app, log_config=LOGGING_CONFIG)
