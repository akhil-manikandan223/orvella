import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Location(Base):
    """A tenant-owned physical site (e.g. 'Main Campus', 'North Wing').

    Deliberately just a free-text address, not the full geo-referenced
    (country/state/city) structure Tenant's own registered address uses -
    that precision exists there for real regulatory/jurisdiction reasons;
    a Location here is internal labeling for grouping People, not a legal
    address, so a plain string is enough.
    """

    __tablename__ = 'locations'
    __table_args__ = (UniqueConstraint('tenant_id', 'name', name='uq_locations_tenant_name'),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey('tenants.id'), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
