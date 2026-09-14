import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TenantUser(Base):
    """A user belonging to one tenant organization (not a platform admin).

    Phase 3 is scoped to a single implicit "tenant admin" role per user -
    there is no roles/permissions table yet, since nothing exists below the
    tenant level (people, departments, etc. are Phase 4) for permissions to
    actually gate. Every TenantUser is, for now, an administrator of their
    own tenant.
    """

    __tablename__ = 'tenant_users'
    __table_args__ = (UniqueConstraint('tenant_id', 'email', name='uq_tenant_users_tenant_email'),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey('tenants.id'), index=True, nullable=False
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
