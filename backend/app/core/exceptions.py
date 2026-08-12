import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

_UNIQUE_VIOLATION_SQLSTATE = '23505'


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                'error': {
                    'code': 'validation_error',
                    'message': 'Invalid request data',
                    'details': exc.errors(),
                }
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={'error': {'code': 'http_error', 'message': exc.detail}},
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
        sqlstate = getattr(getattr(exc, 'orig', None), 'sqlstate', None)
        logger.warning('Integrity error on %s %s: %s', request.method, request.url.path, exc)
        if sqlstate == _UNIQUE_VIOLATION_SQLSTATE:
            return JSONResponse(
                status_code=409,
                content={
                    'error': {
                        'code': 'conflict',
                        'message': 'A record with this value already exists.',
                    }
                },
            )
        return JSONResponse(
            status_code=400,
            content={
                'error': {
                    'code': 'invalid_reference',
                    'message': 'The request references invalid or missing data.',
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception('Unhandled exception')
        return JSONResponse(
            status_code=500,
            content={
                'error': {'code': 'internal_error', 'message': 'An unexpected error occurred'}
            },
        )
