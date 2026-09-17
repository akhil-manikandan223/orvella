import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RefreshToken(Base):
    """A server-side record backing one issued refresh token.

    Shared across both auth domains (platform_admin and tenant_user) rather
    than duplicated per-domain - subject_type/subject_id is a polymorphic
    reference (no DB-level FK, since it points at one of two different
    tables depending on subject_type; referential integrity here is
    enforced in the service layer instead).

    Only the SHA-256 hash of the actual token is ever stored (see
    app.core.security.hash_refresh_token) - the raw token is a bearer
    credential and must never be persisted or logged.

    Rotation: each successful refresh revokes this row and creates a new one
    linked via replaced_by_id, rather than reusing the same row. This lets a
    replayed (already-rotated) token be recognized as reuse - a strong
    signal of theft - rather than silently accepted.
    """

    __tablename__ = 'refresh_tokens'
    __table_args__ = (
        CheckConstraint(
            "subject_type IN ('platform_admin', 'tenant_user')",
            name='ck_refresh_tokens_subject_type',
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    subject_type: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), index=True, nullable=False)
    # Only meaningful for subject_type='tenant_user' - re-checked on refresh
    # the same way the access token's tenant_id claim is, so a refresh token
    # minted on one tenant's subdomain can't mint access tokens for another.
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    replaced_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey('refresh_tokens.id'), nullable=True
    )
