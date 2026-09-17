from fastapi import Response

from app.core.config import Settings

# Two distinct cookie names (not one shared one): a platform admin and a
# tenant user could both be signed in in the same browser at once (e.g. two
# tabs, one per subdomain), and each cookie's path scopes it to only the
# auth endpoints that need it - it's never sent on ordinary API calls.
PLATFORM_ADMIN_COOKIE_NAME = 'orvella_pa_refresh'
PLATFORM_ADMIN_COOKIE_PATH = '/api/v1/auth'

TENANT_USER_COOKIE_NAME = 'orvella_tu_refresh'
TENANT_USER_COOKIE_PATH = '/api/v1/tenant/auth'


def set_refresh_cookie(
    response: Response,
    *,
    name: str,
    path: str,
    value: str,
    max_age_days: int,
    settings: Settings,
) -> None:
    response.set_cookie(
        key=name,
        value=value,
        max_age=max_age_days * 24 * 60 * 60,
        path=path,
        httponly=True,
        # Secure requires HTTPS, which local dev (plain http://) doesn't
        # have - a Secure cookie set locally would simply never come back.
        secure=settings.environment == 'production',
        samesite='lax',
    )


def clear_refresh_cookie(response: Response, *, name: str, path: str) -> None:
    response.delete_cookie(key=name, path=path)
