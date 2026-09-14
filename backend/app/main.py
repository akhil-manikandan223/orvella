from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

import app.core.audit  # noqa: F401 - registers the after_flush audit listener
from app.api.v1.router import api_router
from app.api.v1.routes import health
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.middleware.request_context import RequestContextMiddleware

_STATIC_DIR = Path(__file__).parent / 'static'
# Populated only by the production image (Dockerfile.production copies the
# Angular build's dist/frontend/browser here) - absent in local dev, where
# the frontend runs separately via `ng serve`. Serving it from the same
# FastAPI origin (rather than a separate static host) matters for real
# reasons, not just convenience: tenant subdomains are resolved from each
# request's Host header, so the API must be reachable on the SAME origin
# the tenant's page loaded from - a cross-origin API host would never see
# the right subdomain.
_FRONTEND_DIR = Path(__file__).parent / 'frontend_dist'


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()

    # docs_url=None + a custom /docs route below: the only way to override
    # Swagger UI's favicon (there's no FastAPI() constructor param for it).
    app = FastAPI(title='Orvella API', version='0.1.0', docs_url=None)

    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_origin_regex=settings.cors_origin_regex,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    register_exception_handlers(app)

    app.mount('/static', StaticFiles(directory=_STATIC_DIR), name='static')

    @app.get('/docs', include_in_schema=False)
    async def swagger_ui_html() -> HTMLResponse:
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f'{app.title} - Swagger UI',
            swagger_favicon_url='/static/favicon.png',
        )

    app.include_router(health.router)
    app.include_router(api_router, prefix='/api/v1')

    # Registered last, and only if present, so it never shadows the routes
    # above (a route added after these only gets a chance once /api/*,
    # /health, /docs, and /static have all failed to match).
    #
    # Not a StaticFiles(html=True) mount: that only auto-serves index.html
    # for "/" itself, not for arbitrary client-side routes like /login or
    # /dashboard - those would 404 at the server before Angular's router
    # ever loads. This catch-all serves the real file when one exists
    # (JS/CSS/assets) and falls back to index.html otherwise, which is what
    # SPA client-side routing actually needs.
    if _FRONTEND_DIR.is_dir():
        _FRONTEND_INDEX = _FRONTEND_DIR / 'index.html'

        @app.get('/{full_path:path}', include_in_schema=False)
        async def serve_frontend(full_path: str) -> FileResponse:
            candidate = _FRONTEND_DIR / full_path
            if full_path and candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(_FRONTEND_INDEX)

    return app


app = create_app()
