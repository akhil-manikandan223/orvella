import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OrganizationCategory(Base):
    """A top-level industry classification (e.g. Education, Healthcare)."""

    __tablename__ = 'organization_categories'

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class OrganizationType(Base):
    """A classification within a category (e.g. 'High School' under Education).

    Slug uniqueness is scoped to the category, not global.
    """

    __tablename__ = 'organization_types'
    __table_args__ = (
        UniqueConstraint(
            'organization_category_id',
            'slug',
            name='uq_organization_types_organization_category_id',
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_category_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey('organization_categories.id'), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(150), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class OrganizationTypeFeatureTemplate(Base):
    """A feature recommended by default for tenants of a given organization type.

    Purely advisory: consulted once at tenant-creation time to pre-populate
    TenantFeature rows, never re-consulted afterward. TenantFeature remains
    the single enforced source of truth for what's actually on for a tenant.
    """

    __tablename__ = 'organization_type_feature_templates'
    __table_args__ = (
        UniqueConstraint(
            'organization_type_id',
            'feature_id',
            name='uq_organization_type_feature_templates_organization_type_id',
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_type_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey('organization_types.id'), index=True, nullable=False
    )
    feature_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey('features.id'), index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
