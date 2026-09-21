import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PlatformAdmin(Base):
    """A platform/super-admin operator of Orvella itself.

    Intentionally has no tenant_id: platform admins operate the platform,
    not any single tenant, and are not owned by one.
    """

    __tablename__ = 'platform_admins'
    __table_args__ = (
        CheckConstraint(
            "theme_preference IN ('light', 'dark', 'system')",
            name='ck_platform_admins_theme_preference',
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Per-user so it can't leak between accounts sharing a browser, which is
    # exactly what a single localStorage key did before.
    theme_preference: Mapped[str] = mapped_column(String(10), default='system', nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
