from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import delete

from app.core.security import hash_password
from app.domains.audit_log.models import AuditLog
from app.domains.platform_admin.models import PlatformAdmin
from app.domains.platform_admin.repository import PlatformAdminRepository
from tests.conftest import TestSessionLocal

TEST_EMAIL = 'test-admin@orvella.com'
TEST_PASSWORD = 'correct-horse-battery-staple'


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
