import uuid
from collections.abc import Awaitable, Callable
from functools import partial

from httpx import AsyncClient

from tests.conftest import (
    delete_audit_logs_by_changes,
    delete_feature,
    delete_organization_category,
    delete_organization_type,
)

Cleanup = list[Callable[[], Awaitable[None]]]


def _unique_key(prefix: str) -> str:
    return f'{prefix}-{uuid.uuid4().hex[:8]}'


async def _get_audit_logs(
    client: AsyncClient, headers: dict[str, str], *, entity_id: str
) -> list[dict]:
    response = await client.get(
        '/api/v1/platform-admin/audit-logs', params={'entity_id': entity_id}, headers=headers
    )
    assert response.status_code == 200
    return response.json()


async def test_create_feature_is_audited(
    client: AsyncClient,
    platform_admin_auth_headers: dict[str, str],
    cleanup: Cleanup,
) -> None:
    key = _unique_key('feature')
    create_response = await client.post(
        '/api/v1/platform-admin/features',
        json={'key': key, 'name': 'Attendance'},
        headers=platform_admin_auth_headers,
    )
    assert create_response.status_code == 201
    feature_id = create_response.json()['id']
    cleanup.append(partial(delete_feature, feature_id))

    logs = await _get_audit_logs(client, platform_admin_auth_headers, entity_id=feature_id)
    assert len(logs) == 1
    log = logs[0]
    assert log['action'] == 'create'
    assert log['entity_type'] == 'features'
    assert log['entity_id'] == feature_id
    assert log['actor_type'] == 'platform_admin'
    assert log['changes']['key'] == key
    assert log['changes']['name'] == 'Attendance'
    assert log['changes']['id'] == feature_id


async def test_update_feature_is_audited_with_diff(
    client: AsyncClient,
    platform_admin_auth_headers: dict[str, str],
    cleanup: Cleanup,
) -> None:
    create_response = await client.post(
        '/api/v1/platform-admin/features',
        json={'key': _unique_key('feature'), 'name': 'Attendance'},
        headers=platform_admin_auth_headers,
    )
    feature_id = create_response.json()['id']
    cleanup.append(partial(delete_feature, feature_id))

    await client.patch(
        f'/api/v1/platform-admin/features/{feature_id}',
        json={'name': 'Renamed Feature'},
        headers=platform_admin_auth_headers,
    )

    logs = await _get_audit_logs(client, platform_admin_auth_headers, entity_id=feature_id)
    update_logs = [log for log in logs if log['action'] == 'update']
    assert len(update_logs) == 1
    changes = update_logs[0]['changes']
    assert changes['name'] == {'old': 'Attendance', 'new': 'Renamed Feature'}
    assert 'key' not in changes
    assert 'id' not in changes


async def test_detach_template_feature_is_audited_as_delete(
    client: AsyncClient,
    platform_admin_auth_headers: dict[str, str],
    cleanup: Cleanup,
) -> None:
    category_response = await client.post(
        '/api/v1/platform-admin/organization-categories',
        json={'name': 'Education', 'slug': _unique_key('education')},
        headers=platform_admin_auth_headers,
    )
    category_id = category_response.json()['id']
    cleanup.append(partial(delete_organization_category, category_id))

    type_response = await client.post(
        '/api/v1/platform-admin/organization-types',
        json={
            'organization_category_id': category_id,
            'name': 'High School',
            'slug': _unique_key('high-school'),
        },
        headers=platform_admin_auth_headers,
    )
    organization_type_id = type_response.json()['id']
    cleanup.append(partial(delete_organization_type, organization_type_id))

    feature_response = await client.post(
        '/api/v1/platform-admin/features',
        json={'key': _unique_key('feature'), 'name': 'Attendance'},
        headers=platform_admin_auth_headers,
    )
    feature_id = feature_response.json()['id']
    cleanup.append(partial(delete_feature, feature_id))

    await client.post(
        f'/api/v1/platform-admin/organization-types/{organization_type_id}/features/{feature_id}',
        headers=platform_admin_auth_headers,
    )
    await client.delete(
        f'/api/v1/platform-admin/organization-types/{organization_type_id}/features/{feature_id}',
        headers=platform_admin_auth_headers,
    )

    list_response = await client.get(
        '/api/v1/platform-admin/audit-logs',
        params={'entity_type': 'organization_type_feature_templates'},
        headers=platform_admin_auth_headers,
    )
    assert list_response.status_code == 200
    matching = [
        log
        for log in list_response.json()
        if log['changes'].get('organization_type_id') == organization_type_id
        and log['changes'].get('feature_id') == feature_id
    ]
    assert len(matching) == 2
    actions = sorted(log['action'] for log in matching)
    assert actions == ['create', 'delete']

    # The template row's own id was never surfaced to this test (attach/detach
    # both return no body), so its audit rows can't be purged by entity_id.
    await delete_audit_logs_by_changes(
        organization_type_id=organization_type_id, feature_id=feature_id
    )


async def test_failed_create_produces_no_audit_row(
    client: AsyncClient,
    platform_admin_auth_headers: dict[str, str],
    cleanup: Cleanup,
) -> None:
    key = _unique_key('feature')
    first = await client.post(
        '/api/v1/platform-admin/features',
        json={'key': key, 'name': 'Attendance'},
        headers=platform_admin_auth_headers,
    )
    assert first.status_code == 201
    cleanup.append(partial(delete_feature, first.json()['id']))

    second = await client.post(
        '/api/v1/platform-admin/features',
        json={'key': key, 'name': 'Attendance Duplicate'},
        headers=platform_admin_auth_headers,
    )
    assert second.status_code == 409

    list_response = await client.get(
        '/api/v1/platform-admin/audit-logs',
        params={'entity_type': 'features'},
        headers=platform_admin_auth_headers,
    )
    assert list_response.status_code == 200
    matching_key = [log for log in list_response.json() if log['changes'].get('key') == key]
    # Exactly one create for the successful first request, none for the failed second.
    assert len(matching_key) == 1


async def test_audit_logs_never_reference_themselves(
    client: AsyncClient,
    platform_admin_auth_headers: dict[str, str],
    cleanup: Cleanup,
) -> None:
    create_response = await client.post(
        '/api/v1/platform-admin/features',
        json={'key': _unique_key('feature'), 'name': 'Attendance'},
        headers=platform_admin_auth_headers,
    )
    feature_id = create_response.json()['id']
    cleanup.append(partial(delete_feature, feature_id))

    list_response = await client.get(
        '/api/v1/platform-admin/audit-logs', headers=platform_admin_auth_headers
    )
    assert list_response.status_code == 200
    assert all(log['entity_type'] != 'audit_logs' for log in list_response.json())


async def test_list_audit_logs_requires_auth(client: AsyncClient) -> None:
    response = await client.get('/api/v1/platform-admin/audit-logs')
    assert response.status_code == 401
