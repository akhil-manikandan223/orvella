import uuid
from collections.abc import Awaitable, Callable
from functools import partial

from httpx import AsyncClient
from sqlalchemy import delete

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password
from app.domains.attendance.models import AttendanceRecord
from app.domains.auth_session.models import RefreshToken
from app.domains.feature.repository import FeatureRepository
from app.domains.geo.repository import CityRepository, CountryRepository, StateRepository
from app.domains.organization_taxonomy.repository import (
    OrganizationCategoryRepository,
    OrganizationTypeRepository,
)
from app.domains.person.models import Person
from app.domains.person.repository import PersonRepository
from app.domains.tenant.repository import TenantFeatureRepository, TenantRepository
from app.domains.tenant_user.models import TenantUser
from app.domains.tenant_user.repository import TenantUserRepository
from tests.conftest import (
    TestSessionLocal,
    delete_city,
    delete_country,
    delete_feature,
    delete_organization_category,
    delete_organization_type,
    delete_state,
    delete_tenant,
)

Cleanup = list[Callable[[], Awaitable[None]]]

_settings = get_settings()
BASE_DOMAIN = _settings.base_domain
ATTENDANCE_FEATURE_KEY = 'attendance'


def _unique_slug(prefix: str) -> str:
    return f'{prefix}-{uuid.uuid4().hex[:8]}'


async def _create_organization_type(cleanup: Cleanup) -> uuid.UUID:
    async with TestSessionLocal() as session:
        category = await OrganizationCategoryRepository(session).create(
            name='Education', slug=_unique_slug('education')
        )
        organization_type = await OrganizationTypeRepository(session).create(
            organization_category_id=category.id,
            name='College',
            slug=_unique_slug('college'),
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
            name='Test College',
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


async def _enable_attendance(tenant_id: uuid.UUID, cleanup: Cleanup, *, enabled: bool = True):
    """Puts the attendance feature in the catalog and switches it on for this
    tenant - the gate every route below depends on."""
    async with TestSessionLocal() as session:
        feature_repository = FeatureRepository(session)
        feature = await feature_repository.get_by_key(ATTENDANCE_FEATURE_KEY)
        if feature is None:
            feature = await feature_repository.create(
                key=ATTENDANCE_FEATURE_KEY,
                name='Attendance',
                description='Daily attendance tracking',
                status='active',
            )
            cleanup.append(partial(delete_feature, feature.id))
        tenant_feature = await TenantFeatureRepository(session).create(
            tenant_id=tenant_id, feature_id=feature.id, enabled=enabled
        )
    cleanup.append(partial(_delete_tenant_feature, tenant_feature.id))
    return feature


async def _delete_tenant_feature(tenant_feature_id: uuid.UUID) -> None:
    from app.domains.tenant.models import TenantFeature

    async with TestSessionLocal() as session:
        await session.execute(delete(TenantFeature).where(TenantFeature.id == tenant_feature_id))
        await session.commit()


async def _create_tenant_user(
    tenant_id: uuid.UUID, cleanup: Cleanup, *, role: str
) -> dict[str, str]:
    async with TestSessionLocal() as session:
        user = await TenantUserRepository(session).create(
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
        await session.execute(delete(TenantUser).where(TenantUser.id == user_id))
        await session.commit()


async def _create_person(tenant_id: uuid.UUID, cleanup: Cleanup) -> Person:
    async with TestSessionLocal() as session:
        person = await PersonRepository(session).create(
            tenant_id=tenant_id,
            first_name='Asha',
            last_name=f'Student-{uuid.uuid4().hex[:6]}',
            email=None,
            phone=None,
            category='Student',
            department_id=None,
            location_id=None,
        )
    cleanup.append(partial(_delete_person, person.id))
    return person


async def _delete_person(person_id: uuid.UUID) -> None:
    async with TestSessionLocal() as session:
        await session.execute(
            delete(AttendanceRecord).where(AttendanceRecord.person_id == person_id)
        )
        await session.execute(delete(Person).where(Person.id == person_id))
        await session.commit()


async def test_marking_attendance_is_idempotent(client: AsyncClient, cleanup: Cleanup) -> None:
    slug = _unique_slug('college')
    tenant = await _create_tenant(cleanup, slug=slug)
    await _enable_attendance(tenant.id, cleanup)
    headers = await _create_tenant_user(tenant.id, cleanup, role='admin')
    headers['Host'] = f'{slug}.{BASE_DOMAIN}'
    person = await _create_person(tenant.id, cleanup)

    body = {
        'date': '2026-10-13',
        'records': [{'person_id': str(person.id), 'status': 'absent', 'note': 'Sick'}],
    }
    first = await client.put('/api/v1/tenant/attendance', headers=headers, json=body)
    assert first.status_code == 200
    assert first.json()[0]['status'] == 'absent'

    # Re-marking the same day must correct the record, not create a second
    # one - the whole point of daily granularity.
    body['records'][0]['status'] = 'present'
    second = await client.put('/api/v1/tenant/attendance', headers=headers, json=body)
    assert second.status_code == 200
    assert second.json()[0]['id'] == first.json()[0]['id']
    assert second.json()[0]['status'] == 'present'

    listed = await client.get(
        '/api/v1/tenant/attendance', headers=headers, params={'date': '2026-10-13'}
    )
    assert len(listed.json()) == 1


async def test_absentees_endpoint_excludes_late_and_present(
    client: AsyncClient, cleanup: Cleanup
) -> None:
    slug = _unique_slug('college')
    tenant = await _create_tenant(cleanup, slug=slug)
    await _enable_attendance(tenant.id, cleanup)
    headers = await _create_tenant_user(tenant.id, cleanup, role='admin')
    headers['Host'] = f'{slug}.{BASE_DOMAIN}'
    absent = await _create_person(tenant.id, cleanup)
    late = await _create_person(tenant.id, cleanup)
    present = await _create_person(tenant.id, cleanup)

    await client.put(
        '/api/v1/tenant/attendance',
        headers=headers,
        json={
            'date': '2026-10-13',
            'records': [
                {'person_id': str(absent.id), 'status': 'absent'},
                {'person_id': str(late.id), 'status': 'late'},
                {'person_id': str(present.id), 'status': 'present'},
            ],
        },
    )

    response = await client.get(
        '/api/v1/tenant/attendance/absentees', headers=headers, params={'date': '2026-10-13'}
    )
    assert response.status_code == 200
    assert [r['person_id'] for r in response.json()] == [str(absent.id)]


async def test_summary_counts_by_status(client: AsyncClient, cleanup: Cleanup) -> None:
    slug = _unique_slug('college')
    tenant = await _create_tenant(cleanup, slug=slug)
    await _enable_attendance(tenant.id, cleanup)
    headers = await _create_tenant_user(tenant.id, cleanup, role='admin')
    headers['Host'] = f'{slug}.{BASE_DOMAIN}'
    person = await _create_person(tenant.id, cleanup)

    marks = (('2026-10-01', 'present'), ('2026-10-02', 'absent'), ('2026-10-03', 'absent'))
    for day, status in marks:
        await client.put(
            '/api/v1/tenant/attendance',
            headers=headers,
            json={'date': day, 'records': [{'person_id': str(person.id), 'status': status}]},
        )

    response = await client.get(
        '/api/v1/tenant/attendance/summary',
        headers=headers,
        params={'start': '2026-10-01', 'end': '2026-10-31'},
    )
    assert response.status_code == 200
    summary = next(s for s in response.json() if s['person_id'] == str(person.id))
    assert summary['present'] == 1
    assert summary['absent'] == 2
    assert summary['total'] == 3


async def test_attendance_is_blocked_when_feature_disabled(
    client: AsyncClient, cleanup: Cleanup
) -> None:
    slug = _unique_slug('college')
    tenant = await _create_tenant(cleanup, slug=slug)
    # Feature exists in the catalog but is switched OFF for this tenant.
    await _enable_attendance(tenant.id, cleanup, enabled=False)
    headers = await _create_tenant_user(tenant.id, cleanup, role='admin')
    headers['Host'] = f'{slug}.{BASE_DOMAIN}'

    response = await client.get(
        '/api/v1/tenant/attendance', headers=headers, params={'date': '2026-10-13'}
    )
    assert response.status_code == 403


async def test_attendance_is_blocked_when_tenant_has_no_feature_row(
    client: AsyncClient, cleanup: Cleanup
) -> None:
    slug = _unique_slug('college')
    tenant = await _create_tenant(cleanup, slug=slug)
    headers = await _create_tenant_user(tenant.id, cleanup, role='admin')
    headers['Host'] = f'{slug}.{BASE_DOMAIN}'

    # Never enabled at all: the gate must fail closed rather than default open.
    response = await client.get(
        '/api/v1/tenant/attendance', headers=headers, params={'date': '2026-10-13'}
    )
    assert response.status_code == 403


async def test_member_can_view_but_not_mark(client: AsyncClient, cleanup: Cleanup) -> None:
    slug = _unique_slug('college')
    tenant = await _create_tenant(cleanup, slug=slug)
    await _enable_attendance(tenant.id, cleanup)
    headers = await _create_tenant_user(tenant.id, cleanup, role='member')
    headers['Host'] = f'{slug}.{BASE_DOMAIN}'
    person = await _create_person(tenant.id, cleanup)

    view = await client.get(
        '/api/v1/tenant/attendance', headers=headers, params={'date': '2026-10-13'}
    )
    assert view.status_code == 200

    mark = await client.put(
        '/api/v1/tenant/attendance',
        headers=headers,
        json={'date': '2026-10-13', 'records': [{'person_id': str(person.id), 'status': 'absent'}]},
    )
    assert mark.status_code == 403


async def test_cannot_mark_attendance_for_another_tenants_person(
    client: AsyncClient, cleanup: Cleanup
) -> None:
    slug_a = _unique_slug('college-a')
    slug_b = _unique_slug('college-b')
    tenant_a = await _create_tenant(cleanup, slug=slug_a)
    tenant_b = await _create_tenant(cleanup, slug=slug_b)
    await _enable_attendance(tenant_a.id, cleanup)
    await _enable_attendance(tenant_b.id, cleanup)
    headers_a = await _create_tenant_user(tenant_a.id, cleanup, role='admin')
    headers_a['Host'] = f'{slug_a}.{BASE_DOMAIN}'
    outsider = await _create_person(tenant_b.id, cleanup)

    # The tenant comes from the subdomain but person_id comes from the body -
    # so this is the boundary that stops one tenant writing another's records.
    response = await client.put(
        '/api/v1/tenant/attendance',
        headers=headers_a,
        json={
            'date': '2026-10-13',
            'records': [{'person_id': str(outsider.id), 'status': 'absent'}],
        },
    )
    assert response.status_code == 422


async def test_me_exposes_enabled_feature_keys(client: AsyncClient, cleanup: Cleanup) -> None:
    slug = _unique_slug('college')
    tenant = await _create_tenant(cleanup, slug=slug)
    await _enable_attendance(tenant.id, cleanup)
    headers = await _create_tenant_user(tenant.id, cleanup, role='admin')
    headers['Host'] = f'{slug}.{BASE_DOMAIN}'

    # What the app hides its nav on - the gate itself is still server-side.
    response = await client.get('/api/v1/tenant/auth/me', headers=headers)

    assert response.status_code == 200
    assert ATTENDANCE_FEATURE_KEY in response.json()['features']


async def test_me_omits_disabled_features(client: AsyncClient, cleanup: Cleanup) -> None:
    slug = _unique_slug('college')
    tenant = await _create_tenant(cleanup, slug=slug)
    await _enable_attendance(tenant.id, cleanup, enabled=False)
    headers = await _create_tenant_user(tenant.id, cleanup, role='admin')
    headers['Host'] = f'{slug}.{BASE_DOMAIN}'

    response = await client.get('/api/v1/tenant/auth/me', headers=headers)

    assert ATTENDANCE_FEATURE_KEY not in response.json()['features']


async def test_summary_rejects_backwards_date_range(
    client: AsyncClient, cleanup: Cleanup
) -> None:
    slug = _unique_slug('college')
    tenant = await _create_tenant(cleanup, slug=slug)
    await _enable_attendance(tenant.id, cleanup)
    headers = await _create_tenant_user(tenant.id, cleanup, role='admin')
    headers['Host'] = f'{slug}.{BASE_DOMAIN}'

    response = await client.get(
        '/api/v1/tenant/attendance/summary',
        headers=headers,
        params={'start': '2026-10-31', 'end': '2026-10-01'},
    )
    assert response.status_code == 422
