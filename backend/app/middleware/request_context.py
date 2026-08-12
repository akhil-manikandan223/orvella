import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.core.audit import current_actor_ctx_var
from app.core.logging import request_id_ctx_var


class RequestContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        request_id_token = request_id_ctx_var.set(request_id)
        actor_token = current_actor_ctx_var.set(None)
        try:
            response = await call_next(request)
        finally:
            request_id_ctx_var.reset(request_id_token)
            current_actor_ctx_var.reset(actor_token)
        response.headers['X-Request-ID'] = request_id
        return response
