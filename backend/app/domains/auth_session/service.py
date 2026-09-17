import uuid
from datetime import UTC, datetime, timedelta

from app.core.security import generate_refresh_token, hash_refresh_token
from app.domains.auth_session.models import RefreshToken
from app.domains.auth_session.repository import RefreshTokenRepository


class RefreshTokenInvalidError(Exception):
    """Unknown, expired, revoked, or reused refresh token - the caller
    should treat this as "not signed in", not retry."""


async def issue_refresh_token(
    repository: RefreshTokenRepository,
    *,
    subject_type: str,
    subject_id: uuid.UUID,
    tenant_id: uuid.UUID | None,
    ttl_days: int,
) -> tuple[RefreshToken, str]:
    raw_token = generate_refresh_token()
    row = await repository.create(
        token_hash=hash_refresh_token(raw_token),
        subject_type=subject_type,
        subject_id=subject_id,
        tenant_id=tenant_id,
        expires_at=datetime.now(UTC) + timedelta(days=ttl_days),
    )
    return row, raw_token


def _as_aware_utc(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


async def rotate_refresh_token(
    repository: RefreshTokenRepository,
    *,
    raw_token: str,
    subject_type: str,
    ttl_days: int,
) -> tuple[RefreshToken, str]:
    """Validates raw_token and, if valid, revokes it and issues a fresh one
    in its place (rotation on every use).

    Raises RefreshTokenInvalidError if the token is unknown, expired, or
    already revoked. The already-revoked case specifically means someone
    presented a token that was already rotated out - a possible theft
    signal (the legitimate holder should have the *new* token from the
    rotation, not the old one) - so every other active token for that
    subject is revoked too, forcing a full re-login everywhere rather than
    just rejecting this one attempt.
    """
    existing = await repository.get_by_hash(hash_refresh_token(raw_token))
    if existing is None or existing.subject_type != subject_type:
        raise RefreshTokenInvalidError

    if existing.revoked_at is not None:
        await repository.revoke_all_for_subject(
            subject_type=existing.subject_type, subject_id=existing.subject_id
        )
        raise RefreshTokenInvalidError

    if _as_aware_utc(existing.expires_at) < datetime.now(UTC):
        raise RefreshTokenInvalidError

    new_row, new_raw_token = await issue_refresh_token(
        repository,
        subject_type=existing.subject_type,
        subject_id=existing.subject_id,
        tenant_id=existing.tenant_id,
        ttl_days=ttl_days,
    )
    await repository.revoke(existing, replaced_by_id=new_row.id)
    return new_row, new_raw_token


async def revoke_refresh_token(repository: RefreshTokenRepository, *, raw_token: str) -> None:
    existing = await repository.get_by_hash(hash_refresh_token(raw_token))
    if existing is not None and existing.revoked_at is None:
        await repository.revoke(existing)
