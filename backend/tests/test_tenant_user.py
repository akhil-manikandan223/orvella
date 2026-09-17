import uuid
from collections.abc import Awaitable, Callable
from functools import partial

from httpx import AsyncClient
from sqlalchemy import delete

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password
from app.domains.auth_session.models import RefreshToken
from app.domains.geo.repository import CityRepository, CountryRepository, StateRepository
from app.domains.organization_taxonomy.repository import (
    OrganizationCategoryRepository,
    OrganizationTypeRepository,
)
from app.domains.tenant.repository import TenantRepository
from app.domains.tenant_user.models import TenantUser
from app.domains.tenant_user.repository import TenantUserRepository
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

_settings = get_settings()
BASE_DOMAIN = _settings.base_domain


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
    cleanup.append(partial(delete_country, country.id))
    cleanup.append(partial(delete_state, state.id))
    cleanup.append(partial(delete_city, city.id))
    return country.id, city.id


async def _create_tenant(cleanup: Cleanup, *, slug: str):
    organization_type_id = await _create_organization_type(cleanup)
    country_id, city_id = await _create_country_and_city(cleanup)
    async with TestSessionLocal() as session:
        repository = TenantRepository(session)
        tenant = repository.build(
            name='Test Tenant',
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
        await session.commit()
        await session.refresh(tenant)
    cleanup.append(partial(delete_tenant, tenant.id))
    return tenant


async def _create_tenant_user(
    tenant_id: uuid.UUID, cleanup: Cleanup, *, role: str
) -> tuple[TenantUser, dict[str, str]]:
    """Returns the user plus headers carrying its bearer token - caller must
    still set the 'Host' header to whichever tenant subdomain the request
    should resolve to.
    """
    async with TestSessionLocal() as session:
        repository = TenantUserRepository(session)
        user = await repository.create(
            tenant_id=tenant_id,
            email=f'test-{uuid.uuid4()}@example.com',
            hashed_password=hash_password('irrelevant'),
            role=role,
        )
    cleanup.append(partial(_delete_tenant_user, user.id))
    token = create_access_token(
        subject=str(user.id),
        token_type='tenant_user',
        settings=_settings,
        extra_claims={'tenant_id': str(tenant_id)},
    )
    return user, {'Authorization': f'Bearer {token}'}


async def _delete_tenant_user(user_id: uuid.UUID) -> None:
    async with TestSessionLocal() as session:
        await session.execute(delete(RefreshToken).where(RefreshToken.subject_id == user_id))
        await session.execute(delete(TenantUser).where(TenantUser.id == user_id))
        await session.commit()


async def test_admin_can_list_tenant_users(client: AsyncClient, cleanup: Cleanup) -> None:
    slug = _unique_slug('acme')
    tenant = await _create_tenant(cleanup, slug=slug)
    _, headers = await _create_tenant_user(tenant.id, cleanup, role='admin')
    headers['Host'] = f'{slug}.{BASE_DOMAIN}'

    response = await client.get('/api/v1/tenant/users', headers=headers)

    assert response.status_code == 200


async def test_member_can_view_but_not_manage(client: AsyncClient, cleanup: Cleanup) -> None:
    slug = _unique_slug('acme')
    tenant = await _create_tenant(cleanup, slug=slug)
    _, headers = await _create_tenant_user(tenant.id, cleanup, role='member')
    headers['Host'] = f'{slug}.{BASE_DOMAIN}'

    list_response = await client.get('/api/v1/tenant/users', headers=headers)
    assert list_response.status_code == 200

    create_response = await client.post(
        '/api/v1/tenant/users',
        headers=headers,
        json={'email': f'new-{uuid.uuid4()}@example.com', 'password': 'irrelevant'},
    )
    assert create_response.status_code == 403


async def test_admin_can_create_tenant_user(client: AsyncClient, cleanup: Cleanup) -> None:
    slug = _unique_slug('acme')
    tenant = await _create_tenant(cleanup, slug=slug)
    _, headers = await _create_tenant_user(tenant.id, cleanup, role='admin')
    headers['Host'] = f'{slug}.{BASE_DOMAIN}'
    new_email = f'new-{uuid.uuid4()}@example.com'

    response = await client.post(
        '/api/v1/tenant/users',
        headers=headers,
        json={'email': new_email, 'password': 'irrelevant', 'role': 'member'},
    )

    assert response.status_code == 201
    body = response.json()
    assert body['email'] == new_email
    assert body['role'] == 'member'
    cleanup.append(partial(_delete_tenant_user, uuid.UUID(body['id'])))


async def test_token_from_one_tenant_rejected_on_another(
    client: AsyncClient, cleanup: Cleanup
) -> None:
    slug_a = _unique_slug('tenant-a')
    slug_b = _unique_slug('tenant-b')
    tenant_a = await _create_tenant(cleanup, slug=slug_a)
    tenant_b = await _create_tenant(cleanup, slug=slug_b)
    _, headers = await _create_tenant_user(tenant_a.id, cleanup, role='admin')
    # Token minted for tenant A, but the request arrives on tenant B's host.
    headers['Host'] = f'{slug_b}.{BASE_DOMAIN}'

    response = await client.get('/api/v1/tenant/users', headers=headers)

    assert response.status_code == 401
    assert tenant_b.id != tenant_a.id


TENANT_REFRESH_COOKIE_NAME = 'orvella_tu_refresh'
TEST_PASSWORD = 'correct-horse-battery-staple'


async def _create_tenant_user_with_password(
    tenant_id: uuid.UUID, cleanup: Cleanup, *, role: str = 'admin'
) -> TenantUser:
    async with TestSessionLocal() as session:
        repository = TenantUserRepository(session)
        user = await repository.create(
            tenant_id=tenant_id,
            email=f'test-{uuid.uuid4()}@example.com',
            hashed_password=hash_password(TEST_PASSWORD),
            role=role,
        )
    cleanup.append(partial(_delete_tenant_user, user.id))
    return user


async def test_tenant_login_sets_refresh_cookie(client: AsyncClient, cleanup: Cleanup) -> None:
    slug = _unique_slug('acme')
    tenant = await _create_tenant(cleanup, slug=slug)
    user = await _create_tenant_user_with_password(tenant.id, cleanup)
    host = f'{slug}.{BASE_DOMAIN}'

    response = await client.post(
        '/api/v1/tenant/auth/login',
        headers={'Host': host},
        json={'email': user.email, 'password': TEST_PASSWORD},
    )

    assert response.status_code == 200
    assert client.cookies.get(TENANT_REFRESH_COOKIE_NAME) is not None


async def test_tenant_refresh_issues_a_new_access_token(
    client: AsyncClient, cleanup: Cleanup
) -> None:
    slug = _unique_slug('acme')
    tenant = await _create_tenant(cleanup, slug=slug)
    user = await _create_tenant_user_with_password(tenant.id, cleanup)
    host = f'{slug}.{BASE_DOMAIN}'

    await client.post(
        '/api/v1/tenant/auth/login',
        headers={'Host': host},
        json={'email': user.email, 'password': TEST_PASSWORD},
    )

    refresh_response = await client.post('/api/v1/tenant/auth/refresh', headers={'Host': host})

    assert refresh_response.status_code == 200
    new_access_token = refresh_response.json()['access_token']

    me_response = await client.get(
        '/api/v1/tenant/auth/me',
        headers={'Host': host, 'Authorization': f'Bearer {new_access_token}'},
    )
    assert me_response.status_code == 200
    assert me_response.json()['user']['email'] == user.email


async def test_tenant_refresh_on_wrong_subdomain_is_unauthorized(
    client: AsyncClient, cleanup: Cleanup
) -> None:
    slug_a = _unique_slug('tenant-a')
    slug_b = _unique_slug('tenant-b')
    tenant_a = await _create_tenant(cleanup, slug=slug_a)
    await _create_tenant(cleanup, slug=slug_b)
    user = await _create_tenant_user_with_password(tenant_a.id, cleanup)

    await client.post(
        '/api/v1/tenant/auth/login',
        headers={'Host': f'{slug_a}.{BASE_DOMAIN}'},
        json={'email': user.email, 'password': TEST_PASSWORD},
    )

    # Same browser session (same cookie jar), but the refresh call arrives
    # on a different tenant's subdomain - the cookie's own tenant_id must
    # still be re-checked against the host actually being refreshed from.
    response = await client.post(
        '/api/v1/tenant/auth/refresh', headers={'Host': f'{slug_b}.{BASE_DOMAIN}'}
    )

    assert response.status_code == 401


async def test_tenant_logout_revokes_the_refresh_cookie(
    client: AsyncClient, cleanup: Cleanup
) -> None:
    slug = _unique_slug('acme')
    tenant = await _create_tenant(cleanup, slug=slug)
    user = await _create_tenant_user_with_password(tenant.id, cleanup)
    host = f'{slug}.{BASE_DOMAIN}'

    await client.post(
        '/api/v1/tenant/auth/login',
        headers={'Host': host},
        json={'email': user.email, 'password': TEST_PASSWORD},
    )

    logout_response = await client.post('/api/v1/tenant/auth/logout', headers={'Host': host})
    assert logout_response.status_code == 204

    refresh_after_logout = await client.post(
        '/api/v1/tenant/auth/refresh', headers={'Host': host}
    )
    assert refresh_after_logout.status_code == 401
