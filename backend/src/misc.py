import asyncio
import functools
from collections import defaultdict
from datetime import datetime
from typing import Any, Callable

from fastapi import Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class PlayerAlreadyConnectedError(Exception):
    pass


async def request_validation_handler(
    request: Request, exc: RequestValidationError
) -> Response:
    """
    Exception body template.
    {
        'body': {
            'field': ['validation error message'],
        },
        'path': {
            'param': ['validation error message'],
        },
        'query': {
            'param': ['validation error message'],
        },
    }.
    """

    def dict_of_lists():
        return defaultdict(list)

    body: dict[str | int, dict[str, list[str]]] = defaultdict(dict_of_lists)
    for error in exc.errors():
        if len(error['loc']) == 1:
            # request validation error - request body missing
            loc = error['loc'][0]
            body[loc] = [error.get('msg')]
        else:
            # body/path validation error
            loc, field = error['loc'][0], error['loc'][1]
            body[loc][field].append(error.get('msg'))

    headers = getattr(exc, 'headers', None)
    # cookies = getattr(exc, 'cookies', None)
    if headers:
        return JSONResponse(
            body,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            headers=headers,
            # cookies=cookies, # TODO: Not possible to pass cookies into JSONResponse
        )
    else:
        return JSONResponse(body, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class AsyncCache:
    def __init__(self, ttl: int) -> None:
        self.ttl = ttl
        self._cache: dict[str, tuple[datetime, Any]] = {}
        self._lock = asyncio.Lock()

    def cache(self, ttl: int | None = None) -> Callable[..., Any]:
        ttl = ttl or self.ttl

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs) -> Any:
                async with self._lock:
                    key = f'{func.__module__}.{func.__name__}'
                    if key in self._cache:
                        cached_on, result = self._cache[key]
                        if (datetime.utcnow() - cached_on).seconds < ttl:
                            return result

                    result = await func(*args, **kwargs)
                    cached_on = datetime.utcnow()
                    self._cache[key] = (cached_on, result)
                    return result

            return wrapper

        return decorator

    async def purge(self) -> None:
        async with self._lock:
            self._cache = {}


cache = AsyncCache(60)
