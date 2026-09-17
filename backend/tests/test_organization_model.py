import uuid
from collections.abc import Awaitable, Callable
from functools import partial

from httpx import AsyncClient
from sqlalchemy import delete

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password
from app.domains.auth_session.models import RefreshToken
from app.domains.department.models import Department
from app.domains.geo.repository import CityRepository, CountryRepository, StateRepository
from app.domains.location.models import Location
from app.domains.organization_taxonomy.repository import (
    OrganizationCategoryRepository,
    OrganizationTypeRepository,
)
from app.domains.person.models import Person
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


def _unique_name(prefix: str) -> str:
    return f'{prefix}-{uuid.uuid4().hex[:8]}'


async def _create_organization_type(cleanup: Cleanup) -> uuid.UUID:
    async with TestSessionLocal() as session:
        category = await OrganizationCategoryRepository(session).create(
            name='Education', slug=_unique_name('education')
        )
        organization_type = await OrganizationTypeRepository(session).create(
            organization_category_id=category.id,
            name='High School',
            slug=_unique_name('high-school'),
        )
    cleanup.append(partial(delete_organization_category, category.id))
    cleanup.append(partial(delete_organization_type, organization_type.id))
    return organization_type.id


async def _create_country_and_city(cleanup: Cleanup) -> tuple[uuid.UUID, uuid.UUID]:
    async with TestSessionLocal() as session:
        country = await CountryRepository(session).create(
            name='Testland', slug=_unique_name('testland')
        )
        state = await StateRepository(session).create(
            country_id=country.id, name='Test State', slug=_unique_name('test-state')
        )
        city = await CityRepository(session).create(
            state_id=state.id, district_id=None, name='Test City', slug=_unique_name('test-city')
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
) -> dict[str, str]:
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
    return {'Authorization': f'Bearer {token}'}


async def _delete_tenant_user(user_id: uuid.UUID) -> None:
    async with TestSessionLocal() as session:
        await session.execute(delete(RefreshToken).where(RefreshToken.subject_id == user_id))
        await session.execute(delete(Person).where(Person.tenant_user_id == user_id))
        await session.execute(delete(TenantUser).where(TenantUser.id == user_id))
        await session.commit()


async def _delete_department(department_id: uuid.UUID) -> None:
    async with TestSessionLocal() as session:
        await session.execute(delete(Department).where(Department.id == department_id))
        await session.commit()


async def _delete_location(location_id: uuid.UUID) -> None:
    async with TestSessionLocal() as session:
        await session.execute(delete(Location).where(Location.id == location_id))
        await session.commit()


async def _delete_person(person_id: uuid.UUID) -> None:
    async with TestSessionLocal() as session:
        await session.execute(delete(Person).where(Person.id == person_id))
        await session.commit()


# ---- Departments ----


async def test_admin_can_create_and_list_departments(
    client: AsyncClient, cleanup: Cleanup
) -> None:
    slug = _unique_name('acme')
    tenant = await _create_tenant(cleanup, slug=slug)
    headers = await _create_tenant_user(tenant.id, cleanup, role='admin')
    headers['Host'] = f'{slug}.{BASE_DOMAIN}'

    create_response = await client.post(
        '/api/v1/tenant/departments', headers=headers, json={'name': 'Science'}
    )
    assert create_response.status_code == 201
    department_id = create_response.json()['id']
    cleanup.append(partial(_delete_department, uuid.UUID(department_id)))

    list_response = await client.get('/api/v1/tenant/departments', headers=headers)
    assert list_response.status_code == 200
    assert any(d['id'] == department_id for d in list_response.json())


async def test_member_cannot_manage_departments(client: AsyncClient, cleanup: Cleanup) -> None:
    slug = _unique_name('acme')
    tenant = await _create_tenant(cleanup, slug=slug)
    headers = await _create_tenant_user(tenant.id, cleanup, role='member')
    headers['Host'] = f'{slug}.{BASE_DOMAIN}'

    list_response = await client.get('/api/v1/tenant/departments', headers=headers)
    assert list_response.status_code == 200

    create_response = await client.post(
        '/api/v1/tenant/departments', headers=headers, json={'name': 'Science'}
    )
    assert create_response.status_code == 403


async def test_department_update_and_delete(client: AsyncClient, cleanup: Cleanup) -> None:
    slug = _unique_name('acme')
    tenant = await _create_tenant(cleanup, slug=slug)
    headers = await _create_tenant_user(tenant.id, cleanup, role='admin')
    headers['Host'] = f'{slug}.{BASE_DOMAIN}'

    create_response = await client.post(
        '/api/v1/tenant/departments', headers=headers, json={'name': 'Science'}
    )
    department_id = create_response.json()['id']

    update_response = await client.patch(
        f'/api/v1/tenant/departments/{department_id}',
        headers=headers,
        json={'description': 'Physics, Chemistry, Biology'},
    )
    assert update_response.status_code == 200
    assert update_response.json()['description'] == 'Physics, Chemistry, Biology'

    delete_response = await client.delete(
        f'/api/v1/tenant/departments/{department_id}', headers=headers
    )
    assert delete_response.status_code == 204

    list_response = await client.get('/api/v1/tenant/departments', headers=headers)
    assert not any(d['id'] == department_id for d in list_response.json())


# ---- Locations ----


async def test_admin_can_create_and_list_locations(client: AsyncClient, cleanup: Cleanup) -> None:
    slug = _unique_name('acme')
    tenant = await _create_tenant(cleanup, slug=slug)
    headers = await _create_tenant_user(tenant.id, cleanup, role='admin')
    headers['Host'] = f'{slug}.{BASE_DOMAIN}'

    create_response = await client.post(
        '/api/v1/tenant/locations',
        headers=headers,
        json={'name': 'Main Campus', 'address': '1 School Rd'},
    )
    assert create_response.status_code == 201
    location_id = create_response.json()['id']
    cleanup.append(partial(_delete_location, uuid.UUID(location_id)))

    list_response = await client.get('/api/v1/tenant/locations', headers=headers)
    assert list_response.status_code == 200
    assert any(loc['id'] == location_id for loc in list_response.json())


# ---- People ----


async def test_admin_can_create_person_with_department_and_location(
    client: AsyncClient, cleanup: Cleanup
) -> None:
    slug = _unique_name('acme')
    tenant = await _create_tenant(cleanup, slug=slug)
    headers = await _create_tenant_user(tenant.id, cleanup, role='admin')
    headers['Host'] = f'{slug}.{BASE_DOMAIN}'

    department_response = await client.post(
        '/api/v1/tenant/departments', headers=headers, json={'name': 'Science'}
    )
    department_id = department_response.json()['id']
    cleanup.append(partial(_delete_department, uuid.UUID(department_id)))

    location_response = await client.post(
        '/api/v1/tenant/locations', headers=headers, json={'name': 'Main Campus'}
    )
    location_id = location_response.json()['id']
    cleanup.append(partial(_delete_location, uuid.UUID(location_id)))

    person_response = await client.post(
        '/api/v1/tenant/people',
        headers=headers,
        json={
            'first_name': 'Asha',
            'last_name': 'Verma',
            'category': 'Student',
            'department_id': department_id,
            'location_id': location_id,
        },
    )
    assert person_response.status_code == 201
    body = person_response.json()
    assert body['department_id'] == department_id
    assert body['location_id'] == location_id
    cleanup.append(partial(_delete_person, uuid.UUID(body['id'])))


async def test_person_rejects_department_from_another_tenant(
    client: AsyncClient, cleanup: Cleanup
) -> None:
    slug_a = _unique_name('tenant-a')
    slug_b = _unique_name('tenant-b')
    tenant_a = await _create_tenant(cleanup, slug=slug_a)
    tenant_b = await _create_tenant(cleanup, slug=slug_b)
    headers_a = await _create_tenant_user(tenant_a.id, cleanup, role='admin')
    headers_a['Host'] = f'{slug_a}.{BASE_DOMAIN}'
    headers_b = await _create_tenant_user(tenant_b.id, cleanup, role='admin')
    headers_b['Host'] = f'{slug_b}.{BASE_DOMAIN}'

    department_response = await client.post(
        '/api/v1/tenant/departments', headers=headers_b, json={'name': 'Cardiology'}
    )
    foreign_department_id = department_response.json()['id']
    cleanup.append(partial(_delete_department, uuid.UUID(foreign_department_id)))

    person_response = await client.post(
        '/api/v1/tenant/people',
        headers=headers_a,
        json={
            'first_name': 'Asha',
            'last_name': 'Verma',
            'category': 'Student',
            'department_id': foreign_department_id,
        },
    )

    assert person_response.status_code == 422


async def test_person_list_is_tenant_isolated(client: AsyncClient, cleanup: Cleanup) -> None:
    slug_a = _unique_name('tenant-a')
    slug_b = _unique_name('tenant-b')
    tenant_a = await _create_tenant(cleanup, slug=slug_a)
    tenant_b = await _create_tenant(cleanup, slug=slug_b)
    headers_a = await _create_tenant_user(tenant_a.id, cleanup, role='admin')
    headers_a['Host'] = f'{slug_a}.{BASE_DOMAIN}'
    headers_b = await _create_tenant_user(tenant_b.id, cleanup, role='admin')
    headers_b['Host'] = f'{slug_b}.{BASE_DOMAIN}'

    person_response = await client.post(
        '/api/v1/tenant/people',
        headers=headers_a,
        json={'first_name': 'Asha', 'last_name': 'Verma', 'category': 'Student'},
    )
    person_id = person_response.json()['id']
    cleanup.append(partial(_delete_person, uuid.UUID(person_id)))

    list_response = await client.get('/api/v1/tenant/people', headers=headers_b)
    assert list_response.status_code == 200
    assert not any(p['id'] == person_id for p in list_response.json())
