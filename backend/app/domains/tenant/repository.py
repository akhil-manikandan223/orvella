import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.tenant.models import Tenant, TenantFeature


class TenantRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, tenant_id: uuid.UUID) -> Tenant | None:
        result = await self._session.execute(select(Tenant).where(Tenant.id == tenant_id))
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Tenant | None:
        result = await self._session.execute(select(Tenant).where(Tenant.slug == slug))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Tenant]:
        result = await self._session.execute(select(Tenant).order_by(Tenant.name))
        return list(result.scalars().all())

    def build(
        self,
        *,
        name: str,
        slug: str,
        organization_type_id: uuid.UUID,
        max_users: int | None,
        address_line_1: str,
        country_id: uuid.UUID,
        city_id: uuid.UUID,
        license_number: str,
        key_contact_name: str,
        key_contact_email: str,
        key_contact_phone: str,
        address_line_2: str | None = None,
        state_id: uuid.UUID | None = None,
        postal_code: str | None = None,
        logo_url: str | None = None,
    ) -> Tenant:
        """Construct and stage (add+flush) a Tenant without committing.

        Used by create_tenant, which controls the transaction boundary
        across multiple repositories.
        """
        tenant = Tenant(
            name=name,
            slug=slug,
            organization_type_id=organization_type_id,
            max_users=max_users,
            address_line_1=address_line_1,
            address_line_2=address_line_2,
            country_id=country_id,
            state_id=state_id,
            city_id=city_id,
            postal_code=postal_code,
            license_number=license_number,
            logo_url=logo_url,
            key_contact_name=key_contact_name,
            key_contact_email=key_contact_email,
            key_contact_phone=key_contact_phone,
        )
        self._session.add(tenant)
        return tenant

    async def update(self, tenant: Tenant, **fields: object) -> Tenant:
        """Apply only the given fields (caller decides which via exclude_unset)."""
        for field_name, value in fields.items():
            setattr(tenant, field_name, value)
        await self._session.commit()
        await self._session.refresh(tenant)
        return tenant


class TenantFeatureRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, *, tenant_id: uuid.UUID, feature_id: uuid.UUID) -> TenantFeature | None:
        result = await self._session.execute(
            select(TenantFeature).where(
                TenantFeature.tenant_id == tenant_id, TenantFeature.feature_id == feature_id
            )
        )
        return result.scalar_one_or_none()

    async def list_for_tenant(self, tenant_id: uuid.UUID) -> list[TenantFeature]:
        result = await self._session.execute(
            select(TenantFeature).where(TenantFeature.tenant_id == tenant_id)
        )
        return list(result.scalars().all())

    def build_many(
        self, *, tenant_id: uuid.UUID, feature_ids: Sequence[uuid.UUID], enabled: bool
    ) -> list[TenantFeature]:
        """Construct and stage (add, no flush/commit) TenantFeature rows.

        Used by create_tenant's transaction; does not commit.
        """
        rows = [
            TenantFeature(tenant_id=tenant_id, feature_id=feature_id, enabled=enabled)
            for feature_id in feature_ids
        ]
        self._session.add_all(rows)
        return rows

    async def create(
        self, *, tenant_id: uuid.UUID, feature_id: uuid.UUID, enabled: bool
    ) -> TenantFeature:
        row = TenantFeature(tenant_id=tenant_id, feature_id=feature_id, enabled=enabled)
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return row

    async def set_enabled(self, row: TenantFeature, *, enabled: bool) -> TenantFeature:
        row.enabled = enabled
        await self._session.commit()
        await self._session.refresh(row)
        return row
