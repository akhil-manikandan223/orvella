import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Tenant(Base):
    """An organization using Orvella (e.g. 'Sai Hospital', slug 'saihospital')."""

    __tablename__ = 'tenants'
    __table_args__ = (
        CheckConstraint('max_users IS NULL OR max_users > 0', name='ck_tenants_max_users'),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(63), unique=True, index=True, nullable=False)
    organization_type_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey('organization_types.id'), index=True, nullable=False
    )
    # Optional seat cap for cost control. Null = unlimited. Schema only for
    # now - live enforcement needs Phase 3's tenant-user model, which does
    # not exist yet.
    max_users: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    address_line_1: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line_2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # country/city are required; state is optional (not every country uses
    # that administrative layer). These reference the platform-level geo
    # masters (app.domains.geo) - shared, reusable reference data, not
    # created "for" any one tenant.
    country_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey('countries.id'), index=True, nullable=False
    )
    state_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey('states.id'), index=True, nullable=True
    )
    city_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey('cities.id'), index=True, nullable=False
    )
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    license_number: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    # URL only - no upload endpoint/storage backend decided yet.
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Contact metadata only. Provisioning this person as an actual
    # logged-in tenant admin is Phase 3 work (tenant-user model doesn't
    # exist yet) - these columns do not grant any login access.
    key_contact_name: Mapped[str] = mapped_column(String(150), nullable=False)
    key_contact_email: Mapped[str] = mapped_column(String(320), nullable=False)
    key_contact_phone: Mapped[str] = mapped_column(String(30), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class TenantFeature(Base):
    """The single enforced source of truth for whether a feature is on for a tenant.

    Seeded once from the tenant's organization type's default feature
    template at creation time; toggling flips `enabled` on the existing row
    rather than inserting duplicates.
    """

    __tablename__ = 'tenant_features'
    __table_args__ = (
        UniqueConstraint('tenant_id', 'feature_id', name='uq_tenant_features_tenant_id'),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey('tenants.id'), index=True, nullable=False
    )
    feature_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey('features.id'), index=True, nullable=False
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    configuration: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
