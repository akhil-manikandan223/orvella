import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.hostnames import extract_subdomain_label
from app.core.slugs import validate_tenant_slug
from app.domains.feature.models import Feature
from app.domains.feature.repository import FeatureRepository
from app.domains.feature.service import FeatureNotFoundError
from app.domains.geo.repository import CityRepository, CountryRepository
from app.domains.geo.service import CityNotFoundError, CountryNotFoundError
from app.domains.organization_taxonomy.repository import (
    OrganizationTypeFeatureTemplateRepository,
    OrganizationTypeRepository,
)
from app.domains.organization_taxonomy.service import OrganizationTypeNotFoundError
from app.domains.tenant.models import Tenant, TenantFeature
from app.domains.tenant.repository import TenantFeatureRepository, TenantRepository


class TenantNotFoundError(Exception):
    pass


async def create_tenant(
    session: AsyncSession,
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
) -> tuple[Tenant, list[Feature]]:
    """Create a tenant and seed its features from the org type's default template.

    Controls its own transaction boundary (unlike other service functions
    here) because it must write to two tables atomically: the tenant row and
    its initial TenantFeature rows either both succeed or both fail.
    """
    validate_tenant_slug(slug)

    type_repository = OrganizationTypeRepository(session)
    organization_type = await type_repository.get_by_id(organization_type_id)
    if organization_type is None:
        raise OrganizationTypeNotFoundError

    if await CountryRepository(session).get_by_id(country_id) is None:
        raise CountryNotFoundError
    if await CityRepository(session).get_by_id(city_id) is None:
        raise CityNotFoundError

    tenant_repository = TenantRepository(session)
    tenant = tenant_repository.build(
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
    await session.flush()

    template_repository = OrganizationTypeFeatureTemplateRepository(session)
    feature_ids = await template_repository.list_feature_ids_for_type(organization_type_id)

    if feature_ids:
        TenantFeatureRepository(session).build_many(
            tenant_id=tenant.id, feature_ids=feature_ids, enabled=True
        )
        await session.flush()

    await session.commit()
    await session.refresh(tenant)

    features = await FeatureRepository(session).list_by_ids(feature_ids) if feature_ids else []
    return tenant, features


async def list_tenants(repository: TenantRepository) -> list[Tenant]:
    return await repository.list_all()


async def get_tenant_with_features(
    tenant_repository: TenantRepository,
    tenant_feature_repository: TenantFeatureRepository,
    feature_repository: FeatureRepository,
    *,
    tenant_id: uuid.UUID,
) -> tuple[Tenant, list[Feature]]:
    tenant = await tenant_repository.get_by_id(tenant_id)
    if tenant is None:
        raise TenantNotFoundError

    tenant_features = await tenant_feature_repository.list_for_tenant(tenant_id)
    enabled_feature_ids = [tf.feature_id for tf in tenant_features if tf.enabled]
    features = await feature_repository.list_by_ids(enabled_feature_ids)
    return tenant, features


async def update_tenant(repository: TenantRepository, tenant: Tenant, **fields: object) -> Tenant:
    return await repository.update(tenant, **fields)


async def set_tenant_feature_enabled(
    tenant_repository: TenantRepository,
    feature_repository: FeatureRepository,
    tenant_feature_repository: TenantFeatureRepository,
    *,
    tenant_id: uuid.UUID,
    feature_id: uuid.UUID,
    enabled: bool,
) -> TenantFeature:
    if await tenant_repository.get_by_id(tenant_id) is None:
        raise TenantNotFoundError
    if await feature_repository.get_by_id(feature_id) is None:
        raise FeatureNotFoundError

    existing = await tenant_feature_repository.get(tenant_id=tenant_id, feature_id=feature_id)
    if existing is not None:
        return await tenant_feature_repository.set_enabled(existing, enabled=enabled)
    return await tenant_feature_repository.create(
        tenant_id=tenant_id, feature_id=feature_id, enabled=enabled
    )


async def resolve_tenant_by_host(
    repository: TenantRepository, host: str | None, *, base_domain: str
) -> Tenant | None:
    label = extract_subdomain_label(host, base_domain=base_domain)
    if label is None:
        return None
    tenant = await repository.get_by_slug(label)
    if tenant is None or not tenant.is_active:
        return None
    return tenant
