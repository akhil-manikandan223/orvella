import logging
import re

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

_UNIQUE_VIOLATION_SQLSTATE = '23505'

# Postgres' own wording for a unique violation, e.g.
#   duplicate key value violates unique constraint "ix_tenants_slug"
#   DETAIL:  Key (slug)=(kem-school) already exists.
# The DETAIL line is the better source: it names the actual column(s), where
# the constraint name only implies them. Both are parsed out of the message
# text rather than read off the exception, because SQLAlchemy's asyncpg
# dialect wraps the driver error in its own IntegrityError, and that wrapper
# exposes sqlstate but not constraint_name/table_name.
_CONSTRAINT_PATTERN = re.compile(r'unique constraint "([^"]+)"')
_DETAIL_KEY_PATTERN = re.compile(r'Key \(([^)]+)\)=')


def _humanize(column: str) -> str:
    return column.strip().replace('_', ' ')


def _conflicting_field(exc: IntegrityError) -> tuple[str | None, str | None]:
    """Returns (constraint name, human label for the colliding column(s))."""
    text = str(getattr(exc, 'orig', None) or exc)

    constraint_match = _CONSTRAINT_PATTERN.search(text)
    constraint = constraint_match.group(1) if constraint_match else None

    detail_match = _DETAIL_KEY_PATTERN.search(text)
    if not detail_match:
        return constraint, None

    columns = [_humanize(column) for column in detail_match.group(1).split(',') if column.strip()]
    if not columns:
        return constraint, None
    if len(columns) == 1:
        return constraint, columns[0]
    return constraint, f'{", ".join(columns[:-1])} and {columns[-1]}'


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
        constraint, field = _conflicting_field(exc)
        logger.warning(
            'Integrity error on %s %s (constraint=%s): %s',
            request.method,
            request.url.path,
            constraint,
            exc,
        )
        if sqlstate == _UNIQUE_VIOLATION_SQLSTATE:
            # Naming the field matters: "a record already exists" on a form
            # with two unique columns (e.g. a tenant's slug and its licence
            # number) leaves no way to tell which one to change.
            message = (
                f'Another record already uses this {field}.'
                if field
                else 'A record with this value already exists.'
            )
            error: dict[str, object] = {'code': 'conflict', 'message': message}
            if constraint:
                error['details'] = {'constraint': constraint, 'field': field}
            return JSONResponse(status_code=409, content={'error': error})
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
