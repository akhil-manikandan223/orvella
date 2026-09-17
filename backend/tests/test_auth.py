from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import delete

from app.core.security import hash_password
from app.domains.audit_log.models import AuditLog
from app.domains.auth_session.models import RefreshToken
from app.domains.platform_admin.models import PlatformAdmin
from app.domains.platform_admin.repository import PlatformAdminRepository
from tests.conftest import TestSessionLocal

TEST_EMAIL = 'test-admin@orvella.com'
TEST_PASSWORD = 'correct-horse-battery-staple'

REFRESH_COOKIE_NAME = 'orvella_pa_refresh'


@pytest_asyncio.fixture
async def seeded_admin() -> AsyncIterator[PlatformAdmin]:
    async with TestSessionLocal() as session:
        repository = PlatformAdminRepository(session)
        admin = await repository.create(
            email=TEST_EMAIL, hashed_password=hash_password(TEST_PASSWORD)
        )
    yield admin
    async with TestSessionLocal() as session:
        await session.execute(delete(PlatformAdmin).where(PlatformAdmin.id == admin.id))
        await session.execute(delete(AuditLog).where(AuditLog.entity_id == admin.id))
        await session.execute(delete(RefreshToken).where(RefreshToken.subject_id == admin.id))
        await session.commit()


async def test_login_and_read_current_admin(
    client: AsyncClient, seeded_admin: PlatformAdmin
) -> None:
    login_response = await client.post(
        '/api/v1/auth/login', json={'email': TEST_EMAIL, 'password': TEST_PASSWORD}
    )
    assert login_response.status_code == 200
    token = login_response.json()['access_token']

    me_response = await client.get('/api/v1/auth/me', headers={'Authorization': f'Bearer {token}'})
    assert me_response.status_code == 200
    assert me_response.json()['email'] == TEST_EMAIL


async def test_me_without_token_is_unauthorized(client: AsyncClient) -> None:
    response = await client.get('/api/v1/auth/me')
    assert response.status_code == 401


async def test_login_with_wrong_password_is_unauthorized(
    client: AsyncClient, seeded_admin: PlatformAdmin
) -> None:
    response = await client.post(
        '/api/v1/auth/login', json={'email': TEST_EMAIL, 'password': 'wrong-password'}
    )
    assert response.status_code == 401


async def test_login_with_unknown_email_is_unauthorized(client: AsyncClient) -> None:
    response = await client.post(
        '/api/v1/auth/login', json={'email': 'nobody@orvella.com', 'password': 'irrelevant'}
    )
    assert response.status_code == 401


async def test_login_sets_refresh_cookie(client: AsyncClient, seeded_admin: PlatformAdmin) -> None:
    response = await client.post(
        '/api/v1/auth/login', json={'email': TEST_EMAIL, 'password': TEST_PASSWORD}
    )
    assert response.status_code == 200
    assert client.cookies.get(REFRESH_COOKIE_NAME) is not None


async def test_refresh_issues_a_new_access_token(
    client: AsyncClient, seeded_admin: PlatformAdmin
) -> None:
    await client.post('/api/v1/auth/login', json={'email': TEST_EMAIL, 'password': TEST_PASSWORD})

    refresh_response = await client.post('/api/v1/auth/refresh')

    assert refresh_response.status_code == 200
    new_access_token = refresh_response.json()['access_token']

    me_response = await client.get(
        '/api/v1/auth/me', headers={'Authorization': f'Bearer {new_access_token}'}
    )
    assert me_response.status_code == 200
    assert me_response.json()['email'] == TEST_EMAIL


async def test_refresh_without_cookie_is_unauthorized(client: AsyncClient) -> None:
    response = await client.post('/api/v1/auth/refresh')
    assert response.status_code == 401


async def test_logout_revokes_and_clears_the_refresh_cookie(
    client: AsyncClient, seeded_admin: PlatformAdmin
) -> None:
    await client.post(
        '/api/v1/auth/login', json={'email': TEST_EMAIL, 'password': TEST_PASSWORD}
    )

    logout_response = await client.post('/api/v1/auth/logout')
    assert logout_response.status_code == 204

    refresh_after_logout = await client.post('/api/v1/auth/refresh')
    assert refresh_after_logout.status_code == 401


async def test_replaying_a_rotated_out_refresh_token_revokes_the_whole_chain(
    client: AsyncClient, seeded_admin: PlatformAdmin
) -> None:
    login_response = await client.post(
        '/api/v1/auth/login', json={'email': TEST_EMAIL, 'password': TEST_PASSWORD}
    )
    stale_token = login_response.cookies.get(REFRESH_COOKIE_NAME)
    assert stale_token is not None

    # A normal refresh rotates the cookie - `legit_token` is the new one
    # from that legitimate rotation, while `stale_token` above is the one
    # that got revoked in the process.
    normal_refresh = await client.post('/api/v1/auth/refresh')
    assert normal_refresh.status_code == 200
    legit_token = normal_refresh.cookies.get(REFRESH_COOKIE_NAME)
    assert legit_token is not None

    # Replaying the stale, already-rotated-out token is a theft signal -
    # this must fail, and must also burn the token the legitimate rotation
    # just issued (defensive mass-revocation of the whole chain). Each
    # token is set explicitly rather than relying on whatever's ambient in
    # the client's own cookie jar, since a failed refresh also clears
    # whatever cookie the jar was holding - that clearing would otherwise
    # mask what's being tested here.
    client.cookies.set(REFRESH_COOKIE_NAME, stale_token)
    replay_response = await client.post('/api/v1/auth/refresh')
    assert replay_response.status_code == 401

    client.cookies.set(REFRESH_COOKIE_NAME, legit_token)
    legitimate_refresh_after_replay = await client.post('/api/v1/auth/refresh')
    assert legitimate_refresh_after_replay.status_code == 401
