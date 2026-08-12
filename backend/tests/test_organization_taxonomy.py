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


def _unique_slug(prefix: str) -> str:
    return f'{prefix}-{uuid.uuid4().hex[:8]}'


async def _create_category(client: AsyncClient, headers: dict[str, str], cleanup: Cleanup) -> dict:
    response = await client.post(
        '/api/v1/platform-admin/organization-categories',
        json={'name': 'Education', 'slug': _unique_slug('education')},
        headers=headers,
    )
    assert response.status_code == 201
    category = response.json()
    cleanup.append(partial(delete_organization_category, category['id']))
    return category


async def _create_feature(client: AsyncClient, headers: dict[str, str], cleanup: Cleanup) -> dict:
    response = await client.post(
        '/api/v1/platform-admin/features',
        json={'key': _unique_slug('feature'), 'name': 'Attendance'},
        headers=headers,
    )
    assert response.status_code == 201
    feature = response.json()
    cleanup.append(partial(delete_feature, feature['id']))
    return feature


async def _create_type(
    client: AsyncClient, headers: dict[str, str], cleanup: Cleanup, *, category_id: str, name: str
) -> dict:
    slug_prefix = name.lower().replace(' ', '-')
    response = await client.post(
        '/api/v1/platform-admin/organization-types',
        json={
            'organization_category_id': category_id,
            'name': name,
            'slug': _unique_slug(slug_prefix),
        },
        headers=headers,
    )
    assert response.status_code == 201
    organization_type = response.json()
    cleanup.append(partial(delete_organization_type, organization_type['id']))
    return organization_type


async def test_create_and_list_category(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    category = await _create_category(client, platform_admin_auth_headers, cleanup)

    list_response = await client.get(
        '/api/v1/platform-admin/organization-categories', headers=platform_admin_auth_headers
    )
    assert list_response.status_code == 200
    assert any(c['id'] == category['id'] for c in list_response.json())


async def test_duplicate_category_slug_is_conflict(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    slug = _unique_slug('healthcare')
    payload = {'name': 'Healthcare', 'slug': slug}
    first = await client.post(
        '/api/v1/platform-admin/organization-categories',
        json=payload,
        headers=platform_admin_auth_headers,
    )
    assert first.status_code == 201
    cleanup.append(partial(delete_organization_category, first.json()['id']))

    second = await client.post(
        '/api/v1/platform-admin/organization-categories',
        json=payload,
        headers=platform_admin_auth_headers,
    )
    assert second.status_code == 409


async def test_create_type_under_unknown_category_is_not_found(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str]
) -> None:
    response = await client.post(
        '/api/v1/platform-admin/organization-types',
        json={
            'organization_category_id': str(uuid.uuid4()),
            'name': 'High School',
            'slug': _unique_slug('high-school'),
        },
        headers=platform_admin_auth_headers,
    )
    assert response.status_code == 404


async def test_create_and_list_types_under_category(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    category = await _create_category(client, platform_admin_auth_headers, cleanup)
    await _create_type(
        client, platform_admin_auth_headers, cleanup, category_id=category['id'], name='High School'
    )

    list_response = await client.get(
        '/api/v1/platform-admin/organization-types',
        params={'organization_category_id': category['id']},
        headers=platform_admin_auth_headers,
    )
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


async def test_duplicate_type_slug_within_same_category_is_conflict(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    category = await _create_category(client, platform_admin_auth_headers, cleanup)
    slug = _unique_slug('kindergarten')
    payload = {'organization_category_id': category['id'], 'name': 'Kindergarten', 'slug': slug}

    first = await client.post(
        '/api/v1/platform-admin/organization-types',
        json=payload,
        headers=platform_admin_auth_headers,
    )
    assert first.status_code == 201
    cleanup.append(partial(delete_organization_type, first.json()['id']))

    second = await client.post(
        '/api/v1/platform-admin/organization-types',
        json=payload,
        headers=platform_admin_auth_headers,
    )
    assert second.status_code == 409


async def test_same_type_slug_allowed_across_different_categories(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    category_a = await _create_category(client, platform_admin_auth_headers, cleanup)
    category_b = await _create_category(client, platform_admin_auth_headers, cleanup)
    slug = _unique_slug('general')

    first = await client.post(
        '/api/v1/platform-admin/organization-types',
        json={'organization_category_id': category_a['id'], 'name': 'General', 'slug': slug},
        headers=platform_admin_auth_headers,
    )
    second = await client.post(
        '/api/v1/platform-admin/organization-types',
        json={'organization_category_id': category_b['id'], 'name': 'General', 'slug': slug},
        headers=platform_admin_auth_headers,
    )
    assert first.status_code == 201
    cleanup.append(partial(delete_organization_type, first.json()['id']))
    assert second.status_code == 201
    cleanup.append(partial(delete_organization_type, second.json()['id']))


async def test_attach_list_detach_template_features(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    category = await _create_category(client, platform_admin_auth_headers, cleanup)
    organization_type = await _create_type(
        client, platform_admin_auth_headers, cleanup, category_id=category['id'], name='College'
    )
    feature = await _create_feature(client, platform_admin_auth_headers, cleanup)
    organization_type_id = organization_type['id']

    attach_response = await client.post(
        f'/api/v1/platform-admin/organization-types/{organization_type_id}/features/{feature["id"]}',
        headers=platform_admin_auth_headers,
    )
    assert attach_response.status_code == 201

    list_response = await client.get(
        f'/api/v1/platform-admin/organization-types/{organization_type_id}/features',
        headers=platform_admin_auth_headers,
    )
    assert list_response.status_code == 200
    assert [f['id'] for f in list_response.json()] == [feature['id']]

    detach_response = await client.delete(
        f'/api/v1/platform-admin/organization-types/{organization_type_id}/features/{feature["id"]}',
        headers=platform_admin_auth_headers,
    )
    assert detach_response.status_code == 204

    second_detach_response = await client.delete(
        f'/api/v1/platform-admin/organization-types/{organization_type_id}/features/{feature["id"]}',
        headers=platform_admin_auth_headers,
    )
    assert second_detach_response.status_code == 404

    # The attached-then-detached template row's own id was never surfaced to
    # this test, so its audit rows can't be purged by entity_id - match on
    # the recorded field values instead.
    await delete_audit_logs_by_changes(
        organization_type_id=organization_type_id, feature_id=feature['id']
    )


async def test_update_category_success(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    category = await _create_category(client, platform_admin_auth_headers, cleanup)
    response = await client.patch(
        f'/api/v1/platform-admin/organization-categories/{category["id"]}',
        json={'name': 'Renamed Category'},
        headers=platform_admin_auth_headers,
    )
    assert response.status_code == 200
    assert response.json()['name'] == 'Renamed Category'
    assert response.json()['slug'] == category['slug']


async def test_update_category_unknown_id_is_not_found(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str]
) -> None:
    response = await client.patch(
        f'/api/v1/platform-admin/organization-categories/{uuid.uuid4()}',
        json={'name': 'Whatever'},
        headers=platform_admin_auth_headers,
    )
    assert response.status_code == 404


async def test_update_category_duplicate_slug_is_conflict(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    category_a = await _create_category(client, platform_admin_auth_headers, cleanup)
    category_b = await _create_category(client, platform_admin_auth_headers, cleanup)

    response = await client.patch(
        f'/api/v1/platform-admin/organization-categories/{category_b["id"]}',
        json={'slug': category_a['slug']},
        headers=platform_admin_auth_headers,
    )
    assert response.status_code == 409


async def test_update_organization_type_success(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    category = await _create_category(client, platform_admin_auth_headers, cleanup)
    organization_type = await _create_type(
        client, platform_admin_auth_headers, cleanup, category_id=category['id'], name='Vocational'
    )

    response = await client.patch(
        f'/api/v1/platform-admin/organization-types/{organization_type["id"]}',
        json={'name': 'Renamed Type'},
        headers=platform_admin_auth_headers,
    )
    assert response.status_code == 200
    assert response.json()['name'] == 'Renamed Type'


async def test_update_organization_type_unknown_id_is_not_found(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str]
) -> None:
    response = await client.patch(
        f'/api/v1/platform-admin/organization-types/{uuid.uuid4()}',
        json={'name': 'Whatever'},
        headers=platform_admin_auth_headers,
    )
    assert response.status_code == 404


async def test_list_categories_requires_auth(client: AsyncClient) -> None:
    response = await client.get('/api/v1/platform-admin/organization-categories')
    assert response.status_code == 401
