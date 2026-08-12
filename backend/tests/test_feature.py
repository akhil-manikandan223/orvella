import uuid
from collections.abc import Awaitable, Callable
from functools import partial

from httpx import AsyncClient

from tests.conftest import delete_feature


async def test_create_and_list_feature(
    client: AsyncClient,
    platform_admin_auth_headers: dict[str, str],
    cleanup: list[Callable[[], Awaitable[None]]],
) -> None:
    key = f'feature-{uuid.uuid4().hex[:8]}'
    create_response = await client.post(
        '/api/v1/platform-admin/features',
        json={'key': key, 'name': 'Attendance'},
        headers=platform_admin_auth_headers,
    )
    assert create_response.status_code == 201
    feature_id = create_response.json()['id']
    cleanup.append(partial(delete_feature, feature_id))
    assert create_response.json()['key'] == key

    list_response = await client.get(
        '/api/v1/platform-admin/features', headers=platform_admin_auth_headers
    )
    assert list_response.status_code == 200
    assert any(f['key'] == key for f in list_response.json())


async def test_duplicate_feature_key_is_conflict(
    client: AsyncClient,
    platform_admin_auth_headers: dict[str, str],
    cleanup: list[Callable[[], Awaitable[None]]],
) -> None:
    key = f'feature-{uuid.uuid4().hex[:8]}'
    payload = {'key': key, 'name': 'Attendance'}
    first = await client.post(
        '/api/v1/platform-admin/features', json=payload, headers=platform_admin_auth_headers
    )
    assert first.status_code == 201
    cleanup.append(partial(delete_feature, first.json()['id']))

    second = await client.post(
        '/api/v1/platform-admin/features', json=payload, headers=platform_admin_auth_headers
    )
    assert second.status_code == 409


async def test_update_feature_success(
    client: AsyncClient,
    platform_admin_auth_headers: dict[str, str],
    cleanup: list[Callable[[], Awaitable[None]]],
) -> None:
    create_response = await client.post(
        '/api/v1/platform-admin/features',
        json={'key': f'feature-{uuid.uuid4().hex[:8]}', 'name': 'Attendance'},
        headers=platform_admin_auth_headers,
    )
    feature_id = create_response.json()['id']
    cleanup.append(partial(delete_feature, feature_id))

    response = await client.patch(
        f'/api/v1/platform-admin/features/{feature_id}',
        json={'name': 'Renamed Feature', 'status': 'deprecated'},
        headers=platform_admin_auth_headers,
    )
    assert response.status_code == 200
    assert response.json()['name'] == 'Renamed Feature'
    assert response.json()['status'] == 'deprecated'
    assert response.json()['key'] == create_response.json()['key']


async def test_update_feature_unknown_id_is_not_found(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str]
) -> None:
    response = await client.patch(
        f'/api/v1/platform-admin/features/{uuid.uuid4()}',
        json={'name': 'Whatever'},
        headers=platform_admin_auth_headers,
    )
    assert response.status_code == 404


async def test_list_features_requires_auth(client: AsyncClient) -> None:
    response = await client.get('/api/v1/platform-admin/features')
    assert response.status_code == 401
