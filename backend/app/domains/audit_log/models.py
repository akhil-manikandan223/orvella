import uuid
from datetime import datetime

from sqlalchemy import JSON, CheckConstraint, DateTime, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditLog(Base):
    """Immutable record of who changed what, when, and from what to what.

    Written automatically by app.core.audit's after_flush listener - never
    created directly by application code. Rows are never updated or deleted.
    """

    __tablename__ = 'audit_logs'
    __table_args__ = (
        CheckConstraint("action IN ('create', 'update', 'delete')", name='ck_audit_logs_action'),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Nullable: a system action (e.g. the platform-admin seed script) has no
    # authenticated actor.
    actor_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), nullable=True, index=True
    )
    changes: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
