import uuid
from collections.abc import Awaitable, Callable
from functools import partial

from app.domains.geo.repository import CityRepository, CountryRepository, StateRepository
from app.domains.organization_taxonomy.repository import (
    OrganizationCategoryRepository,
    OrganizationTypeRepository,
)
from app.domains.tenant.repository import TenantRepository
from app.domains.tenant.service import resolve_tenant_by_host
from tests.conftest import (
    TestSessionLocal,
    delete_city,
    delete_country,
    delete_organization_category,
    delete_organization_type,
    delete_state,
    delete_tenant,
)

Cleanup = list[Callable[[], Awaitable[None]]]

BASE_DOMAIN = 'orvella.com'


def _unique_slug(prefix: str) -> str:
    return f'{prefix}-{uuid.uuid4().hex[:8]}'


async def _create_organization_type(cleanup: Cleanup) -> uuid.UUID:
    async with TestSessionLocal() as session:
        category = await OrganizationCategoryRepository(session).create(
            name='Education', slug=_unique_slug('education')
        )
        organization_type = await OrganizationTypeRepository(session).create(
            organization_category_id=category.id,
            name='High School',
            slug=_unique_slug('high-school'),
        )
    # Append in creation order (category, then type) - cleanup runs LIFO, so
    # the type (which references the category via FK) is deleted first.
    cleanup.append(partial(delete_organization_category, category.id))
    cleanup.append(partial(delete_organization_type, organization_type.id))
    return organization_type.id


async def _create_country_and_city(cleanup: Cleanup) -> tuple[uuid.UUID, uuid.UUID]:
    async with TestSessionLocal() as session:
        country = await CountryRepository(session).create(
            name='Testland', slug=_unique_slug('testland')
        )
        state = await StateRepository(session).create(
            country_id=country.id, name='Test State', slug=_unique_slug('test-state')
        )
        city = await CityRepository(session).create(
            state_id=state.id, district_id=None, name='Test City', slug=_unique_slug('test-city')
        )
    # Append in creation order (country, state, city) - cleanup runs LIFO.
    cleanup.append(partial(delete_country, country.id))
    cleanup.append(partial(delete_state, state.id))
    cleanup.append(partial(delete_city, city.id))
    return country.id, city.id


async def _create_tenant(
    organization_type_id: uuid.UUID, cleanup: Cleanup, *, slug: str, is_active: bool = True
):
    country_id, city_id = await _create_country_and_city(cleanup)
    async with TestSessionLocal() as session:
        repository = TenantRepository(session)
        tenant = repository.build(
            name='Resolution School',
            slug=slug,
            organization_type_id=organization_type_id,
            max_users=None,
            address_line_1='123 Main Street',
            country_id=country_id,
            city_id=city_id,
            license_number=f'LIC-{uuid.uuid4().hex[:10]}',
            key_contact_name='Priya Sharma',
            key_contact_email='priya@example.com',
            key_contact_phone='+91-9876543210',
        )
        tenant.is_active = is_active
        await session.commit()
        await session.refresh(tenant)
    cleanup.append(partial(delete_tenant, tenant.id))
    return tenant


async def test_resolve_active_tenant_by_host(cleanup: Cleanup) -> None:
    organization_type_id = await _create_organization_type(cleanup)
    slug = _unique_slug('resolveme')
    await _create_tenant(organization_type_id, cleanup, slug=slug)

    async with TestSessionLocal() as session:
        repository = TenantRepository(session)
        tenant = await resolve_tenant_by_host(
            repository, f'{slug}.orvella.com', base_domain=BASE_DOMAIN
        )
    assert tenant is not None
    assert tenant.slug == slug


async def test_resolve_inactive_tenant_returns_none(cleanup: Cleanup) -> None:
    organization_type_id = await _create_organization_type(cleanup)
    slug = _unique_slug('inactive')
    await _create_tenant(organization_type_id, cleanup, slug=slug, is_active=False)

    async with TestSessionLocal() as session:
        repository = TenantRepository(session)
        tenant = await resolve_tenant_by_host(
            repository, f'{slug}.orvella.com', base_domain=BASE_DOMAIN
        )
    assert tenant is None


async def test_resolve_unknown_slug_returns_none() -> None:
    async with TestSessionLocal() as session:
        repository = TenantRepository(session)
        tenant = await resolve_tenant_by_host(
            repository, 'nosuchtenant.orvella.com', base_domain=BASE_DOMAIN
        )
    assert tenant is None


async def test_resolve_bare_base_domain_returns_none() -> None:
    async with TestSessionLocal() as session:
        repository = TenantRepository(session)
        tenant = await resolve_tenant_by_host(repository, 'orvella.com', base_domain=BASE_DOMAIN)
    assert tenant is None
