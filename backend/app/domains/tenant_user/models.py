import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TenantUser(Base):
    """A user belonging to one tenant organization (not a platform admin).

    A small fixed role set (see app.domains.tenant_user.permissions) - not a
    tenant-customizable role builder. 'admin' can manage the tenant's own
    users and settings; 'member' cannot. There is deliberately no separate
    roles/permissions table: the role set and what each role grants are
    small and fixed in code, not data tenants configure themselves.
    """

    __tablename__ = 'tenant_users'
    __table_args__ = (
        UniqueConstraint('tenant_id', 'email', name='uq_tenant_users_tenant_email'),
        CheckConstraint("role IN ('admin', 'member')", name='ck_tenant_users_role'),
        CheckConstraint(
            "theme_preference IN ('light', 'dark', 'system')",
            name='ck_tenant_users_theme_preference',
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey('tenants.id'), index=True, nullable=False
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default='admin', nullable=False)
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
