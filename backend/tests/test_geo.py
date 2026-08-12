import uuid
from collections.abc import Awaitable, Callable
from functools import partial

from httpx import AsyncClient

from tests.conftest import delete_city, delete_country, delete_district, delete_state

Cleanup = list[Callable[[], Awaitable[None]]]


def _unique_slug(prefix: str) -> str:
    return f'{prefix}-{uuid.uuid4().hex[:8]}'


async def _create_country(client: AsyncClient, headers: dict[str, str], cleanup: Cleanup) -> dict:
    response = await client.post(
        '/api/v1/platform-admin/countries',
        json={'name': 'Testland', 'slug': _unique_slug('testland')},
        headers=headers,
    )
    assert response.status_code == 201
    country = response.json()
    cleanup.append(partial(delete_country, country['id']))
    return country


async def _create_state(
    client: AsyncClient, headers: dict[str, str], cleanup: Cleanup, *, country_id: str
) -> dict:
    response = await client.post(
        '/api/v1/platform-admin/states',
        json={'country_id': country_id, 'name': 'Test State', 'slug': _unique_slug('test-state')},
        headers=headers,
    )
    assert response.status_code == 201
    state = response.json()
    cleanup.append(partial(delete_state, state['id']))
    return state


async def _create_district(
    client: AsyncClient, headers: dict[str, str], cleanup: Cleanup, *, state_id: str
) -> dict:
    response = await client.post(
        '/api/v1/platform-admin/districts',
        json={'state_id': state_id, 'name': 'Test District', 'slug': _unique_slug('test-district')},
        headers=headers,
    )
    assert response.status_code == 201
    district = response.json()
    cleanup.append(partial(delete_district, district['id']))
    return district


async def test_create_and_list_country(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    country = await _create_country(client, platform_admin_auth_headers, cleanup)

    list_response = await client.get(
        '/api/v1/platform-admin/countries', headers=platform_admin_auth_headers
    )
    assert list_response.status_code == 200
    assert any(c['id'] == country['id'] for c in list_response.json())


async def test_duplicate_country_slug_is_conflict(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    slug = _unique_slug('duplicateland')
    payload = {'name': 'Duplicateland', 'slug': slug}
    first = await client.post(
        '/api/v1/platform-admin/countries', json=payload, headers=platform_admin_auth_headers
    )
    assert first.status_code == 201
    cleanup.append(partial(delete_country, first.json()['id']))

    second = await client.post(
        '/api/v1/platform-admin/countries', json=payload, headers=platform_admin_auth_headers
    )
    assert second.status_code == 409


async def test_update_country(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    country = await _create_country(client, platform_admin_auth_headers, cleanup)
    response = await client.patch(
        f'/api/v1/platform-admin/countries/{country["id"]}',
        json={'name': 'Renamed Land'},
        headers=platform_admin_auth_headers,
    )
    assert response.status_code == 200
    assert response.json()['name'] == 'Renamed Land'


async def test_update_country_unknown_id_is_not_found(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str]
) -> None:
    response = await client.patch(
        f'/api/v1/platform-admin/countries/{uuid.uuid4()}',
        json={'name': 'Whatever'},
        headers=platform_admin_auth_headers,
    )
    assert response.status_code == 404


async def test_create_state_under_unknown_country_is_not_found(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str]
) -> None:
    response = await client.post(
        '/api/v1/platform-admin/states',
        json={
            'country_id': str(uuid.uuid4()),
            'name': 'Ghost State',
            'slug': _unique_slug('ghost-state'),
        },
        headers=platform_admin_auth_headers,
    )
    assert response.status_code == 404


async def test_create_and_list_states_under_country(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    country = await _create_country(client, platform_admin_auth_headers, cleanup)
    await _create_state(client, platform_admin_auth_headers, cleanup, country_id=country['id'])

    list_response = await client.get(
        '/api/v1/platform-admin/states',
        params={'country_id': country['id']},
        headers=platform_admin_auth_headers,
    )
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


async def test_duplicate_state_slug_within_same_country_is_conflict(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    country = await _create_country(client, platform_admin_auth_headers, cleanup)
    slug = _unique_slug('dup-state')
    payload = {'country_id': country['id'], 'name': 'Dup State', 'slug': slug}

    first = await client.post(
        '/api/v1/platform-admin/states', json=payload, headers=platform_admin_auth_headers
    )
    assert first.status_code == 201
    cleanup.append(partial(delete_state, first.json()['id']))

    second = await client.post(
        '/api/v1/platform-admin/states', json=payload, headers=platform_admin_auth_headers
    )
    assert second.status_code == 409


async def test_same_state_slug_allowed_across_different_countries(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    country_a = await _create_country(client, platform_admin_auth_headers, cleanup)
    country_b = await _create_country(client, platform_admin_auth_headers, cleanup)
    slug = _unique_slug('shared-state')

    first = await client.post(
        '/api/v1/platform-admin/states',
        json={'country_id': country_a['id'], 'name': 'Shared', 'slug': slug},
        headers=platform_admin_auth_headers,
    )
    second = await client.post(
        '/api/v1/platform-admin/states',
        json={'country_id': country_b['id'], 'name': 'Shared', 'slug': slug},
        headers=platform_admin_auth_headers,
    )
    assert first.status_code == 201
    cleanup.append(partial(delete_state, first.json()['id']))
    assert second.status_code == 201
    cleanup.append(partial(delete_state, second.json()['id']))


async def test_update_state(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    country = await _create_country(client, platform_admin_auth_headers, cleanup)
    state = await _create_state(
        client, platform_admin_auth_headers, cleanup, country_id=country['id']
    )
    response = await client.patch(
        f'/api/v1/platform-admin/states/{state["id"]}',
        json={'name': 'Renamed State'},
        headers=platform_admin_auth_headers,
    )
    assert response.status_code == 200
    assert response.json()['name'] == 'Renamed State'


async def test_create_district_under_unknown_state_is_not_found(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str]
) -> None:
    response = await client.post(
        '/api/v1/platform-admin/districts',
        json={
            'state_id': str(uuid.uuid4()),
            'name': 'Ghost District',
            'slug': _unique_slug('ghost-district'),
        },
        headers=platform_admin_auth_headers,
    )
    assert response.status_code == 404


async def test_create_and_list_districts_under_state(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    country = await _create_country(client, platform_admin_auth_headers, cleanup)
    state = await _create_state(
        client, platform_admin_auth_headers, cleanup, country_id=country['id']
    )
    await _create_district(client, platform_admin_auth_headers, cleanup, state_id=state['id'])

    list_response = await client.get(
        '/api/v1/platform-admin/districts',
        params={'state_id': state['id']},
        headers=platform_admin_auth_headers,
    )
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


async def test_update_district(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    country = await _create_country(client, platform_admin_auth_headers, cleanup)
    state = await _create_state(
        client, platform_admin_auth_headers, cleanup, country_id=country['id']
    )
    district = await _create_district(
        client, platform_admin_auth_headers, cleanup, state_id=state['id']
    )
    response = await client.patch(
        f'/api/v1/platform-admin/districts/{district["id"]}',
        json={'name': 'Renamed District'},
        headers=platform_admin_auth_headers,
    )
    assert response.status_code == 200
    assert response.json()['name'] == 'Renamed District'


async def test_create_city_under_unknown_state_is_not_found(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str]
) -> None:
    response = await client.post(
        '/api/v1/platform-admin/cities',
        json={
            'state_id': str(uuid.uuid4()),
            'name': 'Ghost City',
            'slug': _unique_slug('ghost-city'),
        },
        headers=platform_admin_auth_headers,
    )
    assert response.status_code == 404


async def test_create_city_with_unknown_district_is_not_found(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    country = await _create_country(client, platform_admin_auth_headers, cleanup)
    state = await _create_state(
        client, platform_admin_auth_headers, cleanup, country_id=country['id']
    )
    response = await client.post(
        '/api/v1/platform-admin/cities',
        json={
            'state_id': state['id'],
            'district_id': str(uuid.uuid4()),
            'name': 'Ghost City',
            'slug': _unique_slug('ghost-city'),
        },
        headers=platform_admin_auth_headers,
    )
    assert response.status_code == 404


async def test_create_city_without_district_is_allowed(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    country = await _create_country(client, platform_admin_auth_headers, cleanup)
    state = await _create_state(
        client, platform_admin_auth_headers, cleanup, country_id=country['id']
    )
    response = await client.post(
        '/api/v1/platform-admin/cities',
        json={'state_id': state['id'], 'name': 'No District City', 'slug': _unique_slug('city')},
        headers=platform_admin_auth_headers,
    )
    assert response.status_code == 201
    assert response.json()['district_id'] is None
    cleanup.append(partial(delete_city, response.json()['id']))


async def test_create_city_with_district_and_list_filters(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    country = await _create_country(client, platform_admin_auth_headers, cleanup)
    state = await _create_state(
        client, platform_admin_auth_headers, cleanup, country_id=country['id']
    )
    district = await _create_district(
        client, platform_admin_auth_headers, cleanup, state_id=state['id']
    )
    response = await client.post(
        '/api/v1/platform-admin/cities',
        json={
            'state_id': state['id'],
            'district_id': district['id'],
            'name': 'Districted City',
            'slug': _unique_slug('city'),
        },
        headers=platform_admin_auth_headers,
    )
    assert response.status_code == 201
    city = response.json()
    cleanup.append(partial(delete_city, city['id']))

    by_district = await client.get(
        '/api/v1/platform-admin/cities',
        params={'district_id': district['id']},
        headers=platform_admin_auth_headers,
    )
    assert [c['id'] for c in by_district.json()] == [city['id']]


async def test_duplicate_city_slug_within_same_state_is_conflict(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    country = await _create_country(client, platform_admin_auth_headers, cleanup)
    state = await _create_state(
        client, platform_admin_auth_headers, cleanup, country_id=country['id']
    )
    slug = _unique_slug('dup-city')
    payload = {'state_id': state['id'], 'name': 'Dup City', 'slug': slug}

    first = await client.post(
        '/api/v1/platform-admin/cities', json=payload, headers=platform_admin_auth_headers
    )
    assert first.status_code == 201
    cleanup.append(partial(delete_city, first.json()['id']))

    second = await client.post(
        '/api/v1/platform-admin/cities', json=payload, headers=platform_admin_auth_headers
    )
    assert second.status_code == 409


async def test_same_city_slug_allowed_across_different_states(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    country = await _create_country(client, platform_admin_auth_headers, cleanup)
    state_a = await _create_state(
        client, platform_admin_auth_headers, cleanup, country_id=country['id']
    )
    state_b = await _create_state(
        client, platform_admin_auth_headers, cleanup, country_id=country['id']
    )
    slug = _unique_slug('shared-city')

    first = await client.post(
        '/api/v1/platform-admin/cities',
        json={'state_id': state_a['id'], 'name': 'Shared', 'slug': slug},
        headers=platform_admin_auth_headers,
    )
    second = await client.post(
        '/api/v1/platform-admin/cities',
        json={'state_id': state_b['id'], 'name': 'Shared', 'slug': slug},
        headers=platform_admin_auth_headers,
    )
    assert first.status_code == 201
    cleanup.append(partial(delete_city, first.json()['id']))
    assert second.status_code == 201
    cleanup.append(partial(delete_city, second.json()['id']))


async def test_update_city(
    client: AsyncClient, platform_admin_auth_headers: dict[str, str], cleanup: Cleanup
) -> None:
    country = await _create_country(client, platform_admin_auth_headers, cleanup)
    state = await _create_state(
        client, platform_admin_auth_headers, cleanup, country_id=country['id']
    )
    city_response = await client.post(
        '/api/v1/platform-admin/cities',
        json={'state_id': state['id'], 'name': 'Test City', 'slug': _unique_slug('test-city')},
        headers=platform_admin_auth_headers,
    )
    city_id = city_response.json()['id']
    cleanup.append(partial(delete_city, city_id))

    response = await client.patch(
        f'/api/v1/platform-admin/cities/{city_id}',
        json={'name': 'Renamed City'},
        headers=platform_admin_auth_headers,
    )
    assert response.status_code == 200
    assert response.json()['name'] == 'Renamed City'


async def test_list_countries_requires_auth(client: AsyncClient) -> None:
    response = await client.get('/api/v1/platform-admin/countries')
    assert response.status_code == 401


async def test_list_cities_requires_auth(client: AsyncClient) -> None:
    response = await client.get('/api/v1/platform-admin/cities')
    assert response.status_code == 401
