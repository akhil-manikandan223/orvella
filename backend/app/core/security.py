import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

from app.core.config import Settings

_password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return _password_hash.verify(password, hashed_password)


def create_access_token(
    *,
    subject: str,
    token_type: str,
    settings: Settings,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(UTC)
    payload = {
        'sub': subject,
        'type': token_type,
        'iat': now,
        'exp': now + timedelta(minutes=settings.jwt_access_token_expire_minutes),
        **(extra_claims or {}),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, settings: Settings) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


def generate_refresh_token() -> str:
    """A high-entropy random string, not a JWT - refresh tokens are opaque
    and looked up server-side (by hash) rather than self-describing, so they
    can be individually revoked. See app.domains.auth_session.
    """
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    """SHA-256, not argon2: unlike a password, a refresh token is already
    high-entropy random data, not a low-entropy human secret - there's
    nothing for a slow, memory-hard hash to protect against here, and
    argon2's deliberate cost is real latency we don't need to pay on every
    refresh."""
    return hashlib.sha256(token.encode()).hexdigest()
