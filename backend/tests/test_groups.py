"""Groups and the attendance scope derived from supervising them.

The security claim under test: a 'staff' user (the homeroom teacher) may
mark attendance, but only for the people in groups they supervise. The
group picker in the UI is a convenience - these tests pin the boundary to
the API, where it actually lives.
"""

import uuid
from collections.abc import Awaitable, Callable

from httpx import AsyncClient
from sqlalchemy import delete

from app.core.config import get_settings
from app.core.security import decode_access_token
from app.domains.group.models import Group, GroupMember, GroupSupervisor
from tests.conftest import TestSessionLocal
from tests.test_attendance import (
    BASE_DOMAIN,
    _create_person,
    _create_tenant,
    _create_tenant_user,
    _enable_attendance,
    _unique_slug,
)

Cleanup = list[Callable[[], Awaitable[None]]]

_settings = get_settings()


async def _delete_group(group_id: uuid.UUID) -> None:
    async with TestSessionLocal() as session:
        await session.execute(delete(GroupSupervisor).where(GroupSupervisor.group_id == group_id))
        await session.execute(delete(GroupMember).where(GroupMember.group_id == group_id))
        await session.execute(delete(Group).where(Group.id == group_id))
        await session.commit()


def _user_id(headers: dict[str, str]) -> str:
    """The tenant user id out of the bearer token the helper minted."""
    token = headers['Authorization'].removeprefix('Bearer ')
    return decode_access_token(token, _settings)['sub']


async def _setup(cleanup: Cleanup):
    """A tenant with attendance enabled and an admin signed in."""
    slug = _unique_slug('college')
    tenant = await _create_tenant(cleanup, slug=slug)
    await _enable_attendance(tenant.id, cleanup)
    admin = await _create_tenant_user(tenant.id, cleanup, role='admin')
    admin['Host'] = f'{slug}.{BASE_DOMAIN}'
    return admin, slug, tenant


async def _create_group_with(
    client: AsyncClient,
    admin: dict[str, str],
    cleanup: Cleanup,
    *,
    name: str,
    person_ids: list[str],
    supervisor_ids: list[str],
) -> str:
    created = await client.post('/api/v1/tenant/groups', headers=admin, json={'name': name})
    assert created.status_code == 201, created.text
    group_id = created.json()['id']
    # Appended, not inserted: the fixture runs teardown LIFO, so the group
    # has to be registered after the tenant that owns it.
    cleanup.append(_group_cleanup(uuid.UUID(group_id)))

    members = await client.put(
        f'/api/v1/tenant/groups/{group_id}/members',
        headers=admin,
        json={'person_ids': person_ids},
    )
    assert members.status_code == 200, members.text

    supervisors = await client.put(
        f'/api/v1/tenant/groups/{group_id}/supervisors',
        headers=admin,
        json={'tenant_user_ids': supervisor_ids},
    )
    assert supervisors.status_code == 200, supervisors.text
    return group_id


def _group_cleanup(group_id: uuid.UUID) -> Callable[[], Awaitable[None]]:
    async def _run() -> None:
        await _delete_group(group_id)

    return _run


async def test_staff_can_mark_their_own_group(client: AsyncClient, cleanup: Cleanup) -> None:
    admin, slug, tenant = await _setup(cleanup)
    teacher = await _create_tenant_user(tenant.id, cleanup, role='staff')
    teacher['Host'] = f'{slug}.{BASE_DOMAIN}'
    student = await _create_person(tenant.id, cleanup)

    await _create_group_with(
        client,
        admin,
        cleanup,
        name=f'Grade 10-A {uuid.uuid4().hex[:6]}',
        person_ids=[str(student.id)],
        supervisor_ids=[_user_id(teacher)],
    )

    response = await client.put(
        '/api/v1/tenant/attendance',
        headers=teacher,
        json={
            'date': '2026-10-13',
            'records': [{'person_id': str(student.id), 'status': 'present', 'note': None}],
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()[0]['person_id'] == str(student.id)


async def test_staff_cannot_mark_a_group_they_do_not_supervise(
    client: AsyncClient, cleanup: Cleanup
) -> None:
    """The core of the feature: holding Attendance.Manage is not enough."""
    admin, slug, tenant = await _setup(cleanup)
    teacher = await _create_tenant_user(tenant.id, cleanup, role='staff')
    teacher['Host'] = f'{slug}.{BASE_DOMAIN}'
    other_teacher = await _create_tenant_user(tenant.id, cleanup, role='staff')

    mine = await _create_person(tenant.id, cleanup)
    theirs = await _create_person(tenant.id, cleanup)

    await _create_group_with(
        client,
        admin,
        cleanup,
        name=f'Grade 10-A {uuid.uuid4().hex[:6]}',
        person_ids=[str(mine.id)],
        supervisor_ids=[_user_id(teacher)],
    )
    await _create_group_with(
        client,
        admin,
        cleanup,
        name=f'Grade 10-B {uuid.uuid4().hex[:6]}',
        person_ids=[str(theirs.id)],
        supervisor_ids=[_user_id(other_teacher)],
    )

    response = await client.put(
        '/api/v1/tenant/attendance',
        headers=teacher,
        json={
            'date': '2026-10-13',
            'records': [{'person_id': str(theirs.id), 'status': 'absent', 'note': None}],
        },
    )
    assert response.status_code == 403

    # And a batch must not sneak someone in alongside a legitimate person -
    # the whole request is refused, not partially applied.
    mixed = await client.put(
        '/api/v1/tenant/attendance',
        headers=teacher,
        json={
            'date': '2026-10-13',
            'records': [
                {'person_id': str(mine.id), 'status': 'present', 'note': None},
                {'person_id': str(theirs.id), 'status': 'absent', 'note': None},
            ],
        },
    )
    assert mixed.status_code == 403

    listed = await client.get(
        '/api/v1/tenant/attendance', headers=admin, params={'date': '2026-10-13'}
    )
    assert listed.json() == []


async def test_staff_reads_are_scoped_to_supervised_people(
    client: AsyncClient, cleanup: Cleanup
) -> None:
    admin, slug, tenant = await _setup(cleanup)
    teacher = await _create_tenant_user(tenant.id, cleanup, role='staff')
    teacher['Host'] = f'{slug}.{BASE_DOMAIN}'

    mine = await _create_person(tenant.id, cleanup)
    theirs = await _create_person(tenant.id, cleanup)
    await _create_group_with(
        client,
        admin,
        cleanup,
        name=f'Grade 10-A {uuid.uuid4().hex[:6]}',
        person_ids=[str(mine.id)],
        supervisor_ids=[_user_id(teacher)],
    )

    marked = await client.put(
        '/api/v1/tenant/attendance',
        headers=admin,
        json={
            'date': '2026-10-13',
            'records': [
                {'person_id': str(mine.id), 'status': 'absent', 'note': None},
                {'person_id': str(theirs.id), 'status': 'absent', 'note': None},
            ],
        },
    )
    assert marked.status_code == 200

    # The admin sees both; the teacher sees only their own class.
    everyone = await client.get(
        '/api/v1/tenant/attendance', headers=admin, params={'date': '2026-10-13'}
    )
    assert len(everyone.json()) == 2

    scoped = await client.get(
        '/api/v1/tenant/attendance', headers=teacher, params={'date': '2026-10-13'}
    )
    assert [record['person_id'] for record in scoped.json()] == [str(mine.id)]

    absentees = await client.get(
        '/api/v1/tenant/attendance/absentees', headers=teacher, params={'date': '2026-10-13'}
    )
    assert [record['person_id'] for record in absentees.json()] == [str(mine.id)]

    summary = await client.get(
        '/api/v1/tenant/attendance/summary',
        headers=teacher,
        params={'start': '2026-10-13', 'end': '2026-10-13'},
    )
    assert [row['person_id'] for row in summary.json()] == [str(mine.id)]


async def test_staff_supervising_nothing_sees_and_marks_nothing(
    client: AsyncClient, cleanup: Cleanup
) -> None:
    """An empty scope must mean 'nobody', never 'everybody' - the classic way
    a filter like this fails open."""
    admin, slug, tenant = await _setup(cleanup)
    teacher = await _create_tenant_user(tenant.id, cleanup, role='staff')
    teacher['Host'] = f'{slug}.{BASE_DOMAIN}'
    student = await _create_person(tenant.id, cleanup)

    await client.put(
        '/api/v1/tenant/attendance',
        headers=admin,
        json={
            'date': '2026-10-13',
            'records': [{'person_id': str(student.id), 'status': 'absent', 'note': None}],
        },
    )

    listed = await client.get(
        '/api/v1/tenant/attendance', headers=teacher, params={'date': '2026-10-13'}
    )
    assert listed.json() == []

    marked = await client.put(
        '/api/v1/tenant/attendance',
        headers=teacher,
        json={
            'date': '2026-10-13',
            'records': [{'person_id': str(student.id), 'status': 'present', 'note': None}],
        },
    )
    assert marked.status_code == 403


async def test_staff_cannot_appoint_themselves_supervisor(
    client: AsyncClient, cleanup: Cleanup
) -> None:
    """Otherwise the scope is self-service and worth nothing."""
    admin, slug, tenant = await _setup(cleanup)
    teacher = await _create_tenant_user(tenant.id, cleanup, role='staff')
    teacher['Host'] = f'{slug}.{BASE_DOMAIN}'
    student = await _create_person(tenant.id, cleanup)

    group_id = await _create_group_with(
        client,
        admin,
        cleanup,
        name=f'Grade 10-B {uuid.uuid4().hex[:6]}',
        person_ids=[str(student.id)],
        supervisor_ids=[],
    )

    grab = await client.put(
        f'/api/v1/tenant/groups/{group_id}/supervisors',
        headers=teacher,
        json={'tenant_user_ids': [_user_id(teacher)]},
    )
    assert grab.status_code == 403

    enrol = await client.put(
        f'/api/v1/tenant/groups/{group_id}/members',
        headers=teacher,
        json={'person_ids': [str(student.id)]},
    )
    assert enrol.status_code == 403


async def test_group_members_must_belong_to_the_tenant(
    client: AsyncClient, cleanup: Cleanup
) -> None:
    admin, _, _tenant = await _setup(cleanup)
    _other_admin, _other_slug, other_tenant = await _setup(cleanup)
    outsider = await _create_person(other_tenant.id, cleanup)

    created = await client.post(
        '/api/v1/tenant/groups',
        headers=admin,
        json={'name': f'Grade 10-C {uuid.uuid4().hex[:6]}'},
    )
    assert created.status_code == 201, created.text
    group_id = created.json()['id']
    cleanup.append(_group_cleanup(uuid.UUID(group_id)))

    response = await client.put(
        f'/api/v1/tenant/groups/{group_id}/members',
        headers=admin,
        json={'person_ids': [str(outsider.id)]},
    )
    assert response.status_code == 422


async def test_supervised_groups_endpoint_returns_own_rosters(
    client: AsyncClient, cleanup: Cleanup
) -> None:
    admin, slug, tenant = await _setup(cleanup)
    teacher = await _create_tenant_user(tenant.id, cleanup, role='staff')
    teacher['Host'] = f'{slug}.{BASE_DOMAIN}'
    other_teacher = await _create_tenant_user(tenant.id, cleanup, role='staff')

    mine = await _create_person(tenant.id, cleanup)
    theirs = await _create_person(tenant.id, cleanup)
    name = f'Grade 10-A {uuid.uuid4().hex[:6]}'
    await _create_group_with(
        client,
        admin,
        cleanup,
        name=name,
        person_ids=[str(mine.id)],
        supervisor_ids=[_user_id(teacher)],
    )
    await _create_group_with(
        client,
        admin,
        cleanup,
        name=f'Grade 10-B {uuid.uuid4().hex[:6]}',
        person_ids=[str(theirs.id)],
        supervisor_ids=[_user_id(other_teacher)],
    )

    response = await client.get('/api/v1/tenant/groups/supervised', headers=teacher)
    assert response.status_code == 200
    payload = response.json()
    assert [group['name'] for group in payload] == [name]
    assert payload[0]['member_ids'] == [str(mine.id)]
