from collections import defaultdict

from fastapi import APIRouter, Response, status, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

router = APIRouter()


async def request_validation_handler(
    response: Response, exc: RequestValidationError
) -> Response:
    """Exception body template
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
    }
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
    cookies = getattr(exc, 'cookies', None)
    if headers:
        return JSONResponse(
            body,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            headers=headers,
            cookies=cookies,
        )
    else:
        return JSONResponse(body, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
