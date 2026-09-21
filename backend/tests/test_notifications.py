import uuid
from collections.abc import Awaitable, Callable
from functools import partial

from httpx import AsyncClient
from sqlalchemy import delete, select

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password
from app.domains.auth_session.models import RefreshToken
from app.domains.geo.repository import CityRepository, CountryRepository, StateRepository
from app.domains.notification.models import Notification
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
    tenant_id: uuid.UUID, cleanup: Cleanup, *, role: str = 'admin'
) -> tuple[TenantUser, dict[str, str]]:
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
        await session.execute(delete(Notification).where(Notification.tenant_user_id == user_id))
        await session.execute(delete(RefreshToken).where(RefreshToken.subject_id == user_id))
        await session.execute(delete(TenantUser).where(TenantUser.id == user_id))
        await session.commit()


async def _notifications_for(tenant_user_id: uuid.UUID) -> list[Notification]:
    async with TestSessionLocal() as session:
        result = await session.execute(
            select(Notification).where(Notification.tenant_user_id == tenant_user_id)
        )
        return list(result.scalars().all())


async def _seed_notification(
    *, tenant_id: uuid.UUID, tenant_user_id: uuid.UUID, type: str = 'test.event'
) -> Notification:
    async with TestSessionLocal() as session:
        notification = Notification(
            tenant_id=tenant_id,
            tenant_user_id=tenant_user_id,
            type=type,
            title='Test notification',
            message='Something happened.',
        )
        session.add(notification)
        await session.commit()
        await session.refresh(notification)
        return notification


async def test_list_notifications_empty_for_new_user(
    client: AsyncClient, cleanup: Cleanup
) -> None:
    slug = _unique_slug('acme')
    tenant = await _create_tenant(cleanup, slug=slug)
    _, headers = await _create_tenant_user(tenant.id, cleanup)
    headers['Host'] = f'{slug}.{BASE_DOMAIN}'

    response = await client.get('/api/v1/tenant/notifications', headers=headers)

    assert response.status_code == 200
    assert response.json() == []


async def test_deactivating_tenant_user_creates_notification(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    slug = _unique_slug('acme')
    tenant = await _create_tenant(cleanup, slug=slug)
    user, _ = await _create_tenant_user(tenant.id, cleanup)

    response = await client.patch(
        f'/api/v1/platform-admin/tenants/{tenant.id}/users/{user.id}',
        json={'is_active': False},
        headers=platform_admin_auth_headers,
    )
    assert response.status_code == 200

    notifications = await _notifications_for(user.id)
    assert len(notifications) == 1
    assert notifications[0].type == 'account.deactivated'
    assert notifications[0].read_at is None


async def test_reactivating_tenant_user_creates_notification(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    slug = _unique_slug('acme')
    tenant = await _create_tenant(cleanup, slug=slug)
    user, _ = await _create_tenant_user(tenant.id, cleanup)

    await client.patch(
        f'/api/v1/platform-admin/tenants/{tenant.id}/users/{user.id}',
        json={'is_active': False},
        headers=platform_admin_auth_headers,
    )
    await client.patch(
        f'/api/v1/platform-admin/tenants/{tenant.id}/users/{user.id}',
        json={'is_active': True},
        headers=platform_admin_auth_headers,
    )

    notifications = await _notifications_for(user.id)
    types = [n.type for n in notifications]
    assert types == ['account.deactivated', 'account.reactivated']


async def test_role_change_creates_notification(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    slug = _unique_slug('acme')
    tenant = await _create_tenant(cleanup, slug=slug)
    user, _ = await _create_tenant_user(tenant.id, cleanup, role='admin')

    response = await client.patch(
        f'/api/v1/platform-admin/tenants/{tenant.id}/users/{user.id}',
        json={'role': 'member'},
        headers=platform_admin_auth_headers,
    )
    assert response.status_code == 200

    notifications = await _notifications_for(user.id)
    assert len(notifications) == 1
    assert notifications[0].type == 'account.role_changed'
    assert 'member' in notifications[0].message


async def test_unread_count_list_and_mark_read(client: AsyncClient, cleanup: Cleanup) -> None:
    slug = _unique_slug('acme')
    tenant = await _create_tenant(cleanup, slug=slug)
    user, headers = await _create_tenant_user(tenant.id, cleanup)
    headers['Host'] = f'{slug}.{BASE_DOMAIN}'
    notification = await _seed_notification(tenant_id=tenant.id, tenant_user_id=user.id)

    unread_response = await client.get('/api/v1/tenant/notifications/unread-count', headers=headers)
    assert unread_response.status_code == 200
    assert unread_response.json()['unread_count'] == 1

    list_response = await client.get('/api/v1/tenant/notifications', headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]['read_at'] is None

    read_response = await client.post(
        f'/api/v1/tenant/notifications/{notification.id}/read', headers=headers
    )
    assert read_response.status_code == 200
    assert read_response.json()['read_at'] is not None

    unread_after = await client.get('/api/v1/tenant/notifications/unread-count', headers=headers)
    assert unread_after.json()['unread_count'] == 0


async def test_mark_all_read(client: AsyncClient, cleanup: Cleanup) -> None:
    slug = _unique_slug('acme')
    tenant = await _create_tenant(cleanup, slug=slug)
    user, headers = await _create_tenant_user(tenant.id, cleanup)
    headers['Host'] = f'{slug}.{BASE_DOMAIN}'
    await _seed_notification(tenant_id=tenant.id, tenant_user_id=user.id, type='a')
    await _seed_notification(tenant_id=tenant.id, tenant_user_id=user.id, type='b')

    response = await client.post('/api/v1/tenant/notifications/read-all', headers=headers)
    assert response.status_code == 204

    unread_after = await client.get('/api/v1/tenant/notifications/unread-count', headers=headers)
    assert unread_after.json()['unread_count'] == 0


async def test_cannot_mark_another_users_notification_read(
    client: AsyncClient, cleanup: Cleanup
) -> None:
    slug = _unique_slug('acme')
    tenant = await _create_tenant(cleanup, slug=slug)
    owner, _ = await _create_tenant_user(tenant.id, cleanup)
    _, other_headers = await _create_tenant_user(tenant.id, cleanup)
    other_headers['Host'] = f'{slug}.{BASE_DOMAIN}'
    notification = await _seed_notification(tenant_id=tenant.id, tenant_user_id=owner.id)

    response = await client.post(
        f'/api/v1/tenant/notifications/{notification.id}/read', headers=other_headers
    )
    assert response.status_code == 404


async def test_cross_tenant_notification_is_not_visible(
    client: AsyncClient, cleanup: Cleanup
) -> None:
    slug_a = _unique_slug('tenant-a')
    slug_b = _unique_slug('tenant-b')
    tenant_a = await _create_tenant(cleanup, slug=slug_a)
    tenant_b = await _create_tenant(cleanup, slug=slug_b)
    user_a, _ = await _create_tenant_user(tenant_a.id, cleanup)
    _, headers_b = await _create_tenant_user(tenant_b.id, cleanup)
    headers_b['Host'] = f'{slug_b}.{BASE_DOMAIN}'
    notification = await _seed_notification(tenant_id=tenant_a.id, tenant_user_id=user_a.id)

    # Tenant B's list must never include Tenant A's notification.
    list_response = await client.get('/api/v1/tenant/notifications', headers=headers_b)
    assert list_response.status_code == 200
    assert notification.id not in [uuid.UUID(n['id']) for n in list_response.json()]

    read_response = await client.post(
        f'/api/v1/tenant/notifications/{notification.id}/read', headers=headers_b
    )
    assert read_response.status_code == 404
