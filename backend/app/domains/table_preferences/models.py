import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TableColumnPreference(Base):
    """A platform admin's chosen visible columns for one listing table.

    Keyed by (platform_admin_id, table_key) so the preference travels with
    the admin's account across devices/browsers, rather than being stuck in
    one browser's local storage.
    """

    __tablename__ = 'table_column_preferences'
    __table_args__ = (
        UniqueConstraint(
            'platform_admin_id', 'table_key', name='uq_table_column_preferences_admin_table'
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    platform_admin_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey('platform_admins.id'), index=True, nullable=False
    )
    table_key: Mapped[str] = mapped_column(String(100), nullable=False)
    visible_columns: Mapped[list] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
