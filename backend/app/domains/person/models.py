import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Person(Base):
    """A generic, tenant-owned roster entry - a student, a patient, a gym
    member, a staff member, whatever the tenant's organization type calls
    for. Deliberately ONE table for all of it (see `category`) rather than
    separate Student/Patient/Member schemas: the platform doesn't hard-code
    per-industry entities, and every organization type shares the same
    handful of fields (name, contact info, which department/location).

    Distinct from TenantUser: most People never log into Orvella at all
    (most students/patients/members won't). tenant_user_id is the optional
    exception - set only for the subset of People who are also a logged-in
    platform user (typically staff).
    """

    __tablename__ = 'people'

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey('tenants.id'), index=True, nullable=False
    )
    first_name: Mapped[str] = mapped_column(String(150), nullable=False)
    last_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # Free text, not a fixed enum - the tenant's own vocabulary for their
    # organization type ("Student", "Patient", "Member", "Staff", ...),
    # not something the platform enumerates on their behalf.
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    # SET NULL (not the codebase's usual unspecified/RESTRICT default):
    # departments and locations are things a tenant will genuinely
    # reorganize and delete over time, and that must not be blocked by (or
    # cascade-delete) every Person who happened to be assigned to one.
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey('departments.id', ondelete='SET NULL'),
        index=True,
        nullable=True,
    )
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey('locations.id', ondelete='SET NULL'),
        index=True,
        nullable=True,
    )
    tenant_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey('tenant_users.id', ondelete='SET NULL'),
        unique=True,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
