import uuid
from collections.abc import Awaitable, Callable
from functools import partial

from httpx import AsyncClient

from tests.conftest import (
    delete_city,
    delete_country,
    delete_feature,
    delete_organization_category,
    delete_organization_type,
    delete_state,
    delete_tenant,
)

Cleanup = list[Callable[[], Awaitable[None]]]


def _unique_slug(prefix: str) -> str:
    return f'{prefix}-{uuid.uuid4().hex[:8]}'


async def _create_geo(client: AsyncClient, headers: dict[str, str], cleanup: Cleanup) -> dict:
    """Create a throwaway country/state/city, independent of the seeded geo
    data, so these tests don't depend on the exact seed content.
    """
    country_response = await client.post(
        '/api/v1/platform-admin/countries',
        json={'name': 'Testland', 'slug': _unique_slug('testland')},
        headers=headers,
    )
    country_id = country_response.json()['id']
    cleanup.append(partial(delete_country, country_id))

    state_response = await client.post(
        '/api/v1/platform-admin/states',
        json={'country_id': country_id, 'name': 'Test State', 'slug': _unique_slug('test-state')},
        headers=headers,
    )
    state_id = state_response.json()['id']
    cleanup.append(partial(delete_state, state_id))

    city_response = await client.post(
        '/api/v1/platform-admin/cities',
        json={'state_id': state_id, 'name': 'Test City', 'slug': _unique_slug('test-city')},
        headers=headers,
    )
    city_id = city_response.json()['id']
    cleanup.append(partial(delete_city, city_id))

    return {'country_id': country_id, 'state_id': state_id, 'city_id': city_id}


def _tenant_payload(organization_type_id: str, geo: dict, **overrides: object) -> dict:
    payload = {
        'name': 'Sai High School',
        'slug': _unique_slug('school'),
        'organization_type_id': organization_type_id,
        'address_line_1': '123 Main Street',
        'country_id': geo['country_id'],
        'city_id': geo['city_id'],
        'license_number': f'LIC-{uuid.uuid4().hex[:10]}',
        'key_contact_name': 'Priya Sharma',
        'key_contact_email': 'priya@example.com',
        'key_contact_phone': '+91-9876543210',
    }
    payload.update(overrides)
    return payload


async def _create_category_and_type(
    client: AsyncClient, headers: dict[str, str], cleanup: Cleanup
) -> str:
    category_response = await client.post(
        '/api/v1/platform-admin/organization-categories',
        json={'name': 'Education', 'slug': _unique_slug('education')},
        headers=headers,
    )
    category_id = category_response.json()['id']
    cleanup.append(partial(delete_organization_category, category_id))

    type_response = await client.post(
        '/api/v1/platform-admin/organization-types',
        json={
            'organization_category_id': category_id,
            'name': 'High School',
            'slug': _unique_slug('high-school'),
        },
        headers=headers,
    )
    organization_type_id = type_response.json()['id']
    cleanup.append(partial(delete_organization_type, organization_type_id))
    return organization_type_id


async def _create_feature(client: AsyncClient, headers: dict[str, str], cleanup: Cleanup) -> dict:
    response = await client.post(
        '/api/v1/platform-admin/features',
        json={'key': _unique_slug('feature'), 'name': 'Attendance'},
        headers=headers,
    )
    feature = response.json()
    cleanup.append(partial(delete_feature, feature['id']))
    return feature


async def test_create_tenant_auto_populates_template_features(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    organization_type_id = await _create_category_and_type(
        client, platform_admin_auth_headers, cleanup
    )
    geo = await _create_geo(client, platform_admin_auth_headers, cleanup)
    feature = await _create_feature(client, platform_admin_auth_headers, cleanup)
    await client.post(
        f'/api/v1/platform-admin/organization-types/{organization_type_id}/features/{feature["id"]}',
        headers=platform_admin_auth_headers,
    )

    create_response = await client.post(
        '/api/v1/platform-admin/tenants',
        json=_tenant_payload(organization_type_id, geo, slug=_unique_slug('saihighschool')),
        headers=platform_admin_auth_headers,
    )
    assert create_response.status_code == 201
    body = create_response.json()
    cleanup.append(partial(delete_tenant, body['id']))
    assert [f['id'] for f in body['features']] == [feature['id']]


async def test_create_tenant_returns_profile_fields(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    organization_type_id = await _create_category_and_type(
        client, platform_admin_auth_headers, cleanup
    )
    geo = await _create_geo(client, platform_admin_auth_headers, cleanup)
    payload = _tenant_payload(
        organization_type_id,
        geo,
        address_line_2='Suite 4B',
        state_id=geo['state_id'],
        postal_code='600001',
        logo_url='https://example.com/logo.png',
    )

    create_response = await client.post(
        '/api/v1/platform-admin/tenants', json=payload, headers=platform_admin_auth_headers
    )
    assert create_response.status_code == 201
    body = create_response.json()
    cleanup.append(partial(delete_tenant, body['id']))
    assert body['address_line_1'] == payload['address_line_1']
    assert body['address_line_2'] == 'Suite 4B'
    assert body['city_id'] == geo['city_id']
    assert body['state_id'] == geo['state_id']
    assert body['postal_code'] == '600001'
    assert body['country_id'] == geo['country_id']
    assert body['license_number'] == payload['license_number']
    assert body['logo_url'] == 'https://example.com/logo.png'
    assert body['key_contact_name'] == payload['key_contact_name']
    assert body['key_contact_email'] == payload['key_contact_email']
    assert body['key_contact_phone'] == payload['key_contact_phone']


async def test_create_tenant_missing_required_field_is_unprocessable(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    organization_type_id = await _create_category_and_type(
        client, platform_admin_auth_headers, cleanup
    )
    geo = await _create_geo(client, platform_admin_auth_headers, cleanup)
    payload = _tenant_payload(organization_type_id, geo)
    del payload['license_number']

    response = await client.post(
        '/api/v1/platform-admin/tenants', json=payload, headers=platform_admin_auth_headers
    )
    assert response.status_code == 422


async def test_create_tenant_duplicate_license_number_is_conflict(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    organization_type_id = await _create_category_and_type(
        client, platform_admin_auth_headers, cleanup
    )
    geo = await _create_geo(client, platform_admin_auth_headers, cleanup)
    license_number = f'LIC-{uuid.uuid4().hex[:10]}'

    first = await client.post(
        '/api/v1/platform-admin/tenants',
        json=_tenant_payload(organization_type_id, geo, license_number=license_number),
        headers=platform_admin_auth_headers,
    )
    assert first.status_code == 201
    cleanup.append(partial(delete_tenant, first.json()['id']))

    second = await client.post(
        '/api/v1/platform-admin/tenants',
        json=_tenant_payload(organization_type_id, geo, license_number=license_number),
        headers=platform_admin_auth_headers,
    )
    assert second.status_code == 409


async def test_create_tenant_with_template_less_type_has_no_features(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    organization_type_id = await _create_category_and_type(
        client, platform_admin_auth_headers, cleanup
    )
    geo = await _create_geo(client, platform_admin_auth_headers, cleanup)

    create_response = await client.post(
        '/api/v1/platform-admin/tenants',
        json=_tenant_payload(organization_type_id, geo, slug=_unique_slug('emptyschool')),
        headers=platform_admin_auth_headers,
    )
    assert create_response.status_code == 201
    cleanup.append(partial(delete_tenant, create_response.json()['id']))
    assert create_response.json()['features'] == []


async def test_create_tenant_duplicate_slug_is_conflict(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    organization_type_id = await _create_category_and_type(
        client, platform_admin_auth_headers, cleanup
    )
    geo = await _create_geo(client, platform_admin_auth_headers, cleanup)
    slug = _unique_slug('dup-school')
    payload = _tenant_payload(organization_type_id, geo, slug=slug)

    first = await client.post(
        '/api/v1/platform-admin/tenants', json=payload, headers=platform_admin_auth_headers
    )
    assert first.status_code == 201
    cleanup.append(partial(delete_tenant, first.json()['id']))

    second = await client.post(
        '/api/v1/platform-admin/tenants',
        json=_tenant_payload(organization_type_id, geo, slug=slug),
        headers=platform_admin_auth_headers,
    )
    assert second.status_code == 409


async def test_create_tenant_unknown_type_is_not_found(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    geo = await _create_geo(client, platform_admin_auth_headers, cleanup)
    response = await client.post(
        '/api/v1/platform-admin/tenants',
        json=_tenant_payload(str(uuid.uuid4()), geo, slug=_unique_slug('ghost-school')),
        headers=platform_admin_auth_headers,
    )
    assert response.status_code == 404


async def test_create_tenant_unknown_country_is_not_found(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    organization_type_id = await _create_category_and_type(
        client, platform_admin_auth_headers, cleanup
    )
    geo = await _create_geo(client, platform_admin_auth_headers, cleanup)
    response = await client.post(
        '/api/v1/platform-admin/tenants',
        json=_tenant_payload(
            organization_type_id,
            geo,
            slug=_unique_slug('ghost-country'),
            country_id=str(uuid.uuid4()),
        ),
        headers=platform_admin_auth_headers,
    )
    assert response.status_code == 404


async def test_create_tenant_invalid_slug_format_is_unprocessable(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    organization_type_id = await _create_category_and_type(
        client, platform_admin_auth_headers, cleanup
    )
    geo = await _create_geo(client, platform_admin_auth_headers, cleanup)
    response = await client.post(
        '/api/v1/platform-admin/tenants',
        json=_tenant_payload(organization_type_id, geo, slug='Bad_Slug'),
        headers=platform_admin_auth_headers,
    )
    assert response.status_code == 422


async def test_create_tenant_reserved_slug_is_unprocessable(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    organization_type_id = await _create_category_and_type(
        client, platform_admin_auth_headers, cleanup
    )
    geo = await _create_geo(client, platform_admin_auth_headers, cleanup)
    response = await client.post(
        '/api/v1/platform-admin/tenants',
        json=_tenant_payload(organization_type_id, geo, slug='www'),
        headers=platform_admin_auth_headers,
    )
    assert response.status_code == 422


async def test_toggle_tenant_feature_off_then_on(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    organization_type_id = await _create_category_and_type(
        client, platform_admin_auth_headers, cleanup
    )
    geo = await _create_geo(client, platform_admin_auth_headers, cleanup)
    feature = await _create_feature(client, platform_admin_auth_headers, cleanup)
    await client.post(
        f'/api/v1/platform-admin/organization-types/{organization_type_id}/features/{feature["id"]}',
        headers=platform_admin_auth_headers,
    )
    tenant_response = await client.post(
        '/api/v1/platform-admin/tenants',
        json=_tenant_payload(organization_type_id, geo, slug=_unique_slug('toggle-school')),
        headers=platform_admin_auth_headers,
    )
    tenant_id = tenant_response.json()['id']
    cleanup.append(partial(delete_tenant, tenant_id))

    off_response = await client.patch(
        f'/api/v1/platform-admin/tenants/{tenant_id}/features/{feature["id"]}',
        json={'enabled': False},
        headers=platform_admin_auth_headers,
    )
    assert off_response.status_code == 200
    assert off_response.json()['enabled'] is False

    on_response = await client.patch(
        f'/api/v1/platform-admin/tenants/{tenant_id}/features/{feature["id"]}',
        json={'enabled': True},
        headers=platform_admin_auth_headers,
    )
    assert on_response.status_code == 200
    assert on_response.json()['enabled'] is True


async def test_toggle_feature_for_tenant_with_no_starting_features_creates_row(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    organization_type_id = await _create_category_and_type(
        client, platform_admin_auth_headers, cleanup
    )
    geo = await _create_geo(client, platform_admin_auth_headers, cleanup)
    feature = await _create_feature(client, platform_admin_auth_headers, cleanup)
    tenant_response = await client.post(
        '/api/v1/platform-admin/tenants',
        json=_tenant_payload(organization_type_id, geo, slug=_unique_slug('bare-school')),
        headers=platform_admin_auth_headers,
    )
    tenant_id = tenant_response.json()['id']
    cleanup.append(partial(delete_tenant, tenant_id))
    assert tenant_response.json()['features'] == []

    toggle_response = await client.patch(
        f'/api/v1/platform-admin/tenants/{tenant_id}/features/{feature["id"]}',
        json={'enabled': True},
        headers=platform_admin_auth_headers,
    )
    assert toggle_response.status_code == 200
    assert toggle_response.json()['enabled'] is True


async def test_toggle_unknown_tenant_or_feature_is_not_found(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    organization_type_id = await _create_category_and_type(
        client, platform_admin_auth_headers, cleanup
    )
    geo = await _create_geo(client, platform_admin_auth_headers, cleanup)
    feature = await _create_feature(client, platform_admin_auth_headers, cleanup)
    tenant_response = await client.post(
        '/api/v1/platform-admin/tenants',
        json=_tenant_payload(organization_type_id, geo, slug=_unique_slug('lookup-school')),
        headers=platform_admin_auth_headers,
    )
    tenant_id = tenant_response.json()['id']
    cleanup.append(partial(delete_tenant, tenant_id))

    unknown_tenant_response = await client.patch(
        f'/api/v1/platform-admin/tenants/{uuid.uuid4()}/features/{feature["id"]}',
        json={'enabled': True},
        headers=platform_admin_auth_headers,
    )
    assert unknown_tenant_response.status_code == 404

    unknown_feature_response = await client.patch(
        f'/api/v1/platform-admin/tenants/{tenant_id}/features/{uuid.uuid4()}',
        json={'enabled': True},
        headers=platform_admin_auth_headers,
    )
    assert unknown_feature_response.status_code == 404


async def test_update_tenant_max_users_and_is_active(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    organization_type_id = await _create_category_and_type(
        client, platform_admin_auth_headers, cleanup
    )
    geo = await _create_geo(client, platform_admin_auth_headers, cleanup)
    tenant_response = await client.post(
        '/api/v1/platform-admin/tenants',
        json=_tenant_payload(
            organization_type_id, geo, slug=_unique_slug('update-school'), max_users=50
        ),
        headers=platform_admin_auth_headers,
    )
    tenant_id = tenant_response.json()['id']
    cleanup.append(partial(delete_tenant, tenant_id))
    assert tenant_response.json()['max_users'] == 50

    patch_response = await client.patch(
        f'/api/v1/platform-admin/tenants/{tenant_id}',
        json={'is_active': False},
        headers=platform_admin_auth_headers,
    )
    assert patch_response.status_code == 200
    assert patch_response.json()['is_active'] is False
    assert patch_response.json()['max_users'] == 50

    null_max_users_response = await client.patch(
        f'/api/v1/platform-admin/tenants/{tenant_id}',
        json={'max_users': None},
        headers=platform_admin_auth_headers,
    )
    assert null_max_users_response.status_code == 200
    assert null_max_users_response.json()['max_users'] is None


async def test_update_tenant_profile_fields(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    organization_type_id = await _create_category_and_type(
        client, platform_admin_auth_headers, cleanup
    )
    geo = await _create_geo(client, platform_admin_auth_headers, cleanup)
    tenant_response = await client.post(
        '/api/v1/platform-admin/tenants',
        json=_tenant_payload(organization_type_id, geo, slug=_unique_slug('patch-school')),
        headers=platform_admin_auth_headers,
    )
    tenant_id = tenant_response.json()['id']
    cleanup.append(partial(delete_tenant, tenant_id))

    patch_response = await client.patch(
        f'/api/v1/platform-admin/tenants/{tenant_id}',
        json={'address_line_2': 'Building C', 'logo_url': 'https://example.com/new-logo.png'},
        headers=platform_admin_auth_headers,
    )
    assert patch_response.status_code == 200
    assert patch_response.json()['address_line_2'] == 'Building C'
    assert patch_response.json()['logo_url'] == 'https://example.com/new-logo.png'


async def test_list_and_get_tenant(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    organization_type_id = await _create_category_and_type(
        client, platform_admin_auth_headers, cleanup
    )
    geo = await _create_geo(client, platform_admin_auth_headers, cleanup)
    create_response = await client.post(
        '/api/v1/platform-admin/tenants',
        json=_tenant_payload(organization_type_id, geo, slug=_unique_slug('get-school')),
        headers=platform_admin_auth_headers,
    )
    tenant_id = create_response.json()['id']
    cleanup.append(partial(delete_tenant, tenant_id))

    list_response = await client.get(
        '/api/v1/platform-admin/tenants', headers=platform_admin_auth_headers
    )
    assert list_response.status_code == 200
    assert any(t['id'] == tenant_id for t in list_response.json())

    get_response = await client.get(
        f'/api/v1/platform-admin/tenants/{tenant_id}', headers=platform_admin_auth_headers
    )
    assert get_response.status_code == 200
    assert get_response.json()['id'] == tenant_id


async def test_list_tenants_requires_auth(client: AsyncClient) -> None:
    response = await client.get('/api/v1/platform-admin/tenants')
    assert response.status_code == 401
