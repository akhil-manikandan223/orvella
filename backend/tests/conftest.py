import uuid
from collections.abc import AsyncIterator, Awaitable, Callable

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.db.session import get_db
from app.domains.audit_log.models import AuditLog
from app.domains.feature.models import Feature
from app.domains.geo.models import City, Country, District, State
from app.domains.organization_taxonomy.models import (
    OrganizationCategory,
    OrganizationType,
    OrganizationTypeFeatureTemplate,
)
from app.domains.platform_admin.models import PlatformAdmin
from app.domains.platform_admin.repository import PlatformAdminRepository
from app.domains.tenant.models import Tenant, TenantFeature
from app.main import app

# A dedicated engine/session factory for tests, using NullPool: each checkout
# opens a fresh physical connection bound to whichever event loop is
# currently running, which sidesteps pytest-asyncio's per-test event loop
# creation reusing (and crashing on) connections pooled under a prior loop.
# Kept separate from app.db.session's pooled engine, which stays tuned for
# the running app rather than the test harness.
_settings = get_settings()
test_engine = create_async_engine(_settings.database_url, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


async def _override_get_db() -> AsyncIterator:
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = _override_get_db


@pytest_asyncio.fixture(scope='session', autouse=True)
async def _prepare_database() -> AsyncIterator[None]:
    # Only ensures tables exist (idempotent) - deliberately does not drop
    # anything at teardown, since DATABASE_URL may point at a shared local
    # dev database rather than a disposable test database (CI uses its own
    # ephemeral database, so this is a non-issue there). Tests are
    # responsible for cleaning up the specific rows they create.
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://testserver') as ac:
        yield ac


@pytest_asyncio.fixture
async def platform_admin_auth_headers() -> AsyncIterator[dict[str, str]]:
    email = f'test-{uuid.uuid4()}@orvella.com'
    async with TestSessionLocal() as session:
        repository = PlatformAdminRepository(session)
        admin = await repository.create(email=email, hashed_password=hash_password('irrelevant'))

    token = create_access_token(
        subject=str(admin.id), token_type='platform_admin', settings=_settings
    )
    yield {'Authorization': f'Bearer {token}'}

    async with TestSessionLocal() as session:
        await session.execute(delete(PlatformAdmin).where(PlatformAdmin.id == admin.id))
        await session.execute(delete(AuditLog).where(AuditLog.entity_id == admin.id))
        await session.commit()


@pytest_asyncio.fixture
async def cleanup() -> AsyncIterator[list[Callable[[], Awaitable[None]]]]:
    """Register async no-arg callables here (in creation order); they run in
    reverse (LIFO) at teardown, so append parent-before-child (category,
    then type, then feature, then tenant) and dependents get deleted first.
    """
    pending: list[Callable[[], Awaitable[None]]] = []
    yield pending
    for action in reversed(pending):
        await action()


async def delete_audit_logs_for_entity(entity_id: uuid.UUID) -> None:
    async with TestSessionLocal() as session:
        await session.execute(delete(AuditLog).where(AuditLog.entity_id == entity_id))
        await session.commit()


async def delete_audit_logs_by_changes(**filters: object) -> None:
    """Delete audit_logs whose `changes` JSON contains all the given key=value
    pairs (compared as strings). For entities whose own id was never surfaced
    to the test (e.g. a join-table row created and deleted entirely within
    one API call, like attach/detach), there's no entity_id to filter by
    directly - this matches on the row's recorded field values instead.
    """
    async with TestSessionLocal() as session:
        result = await session.execute(select(AuditLog))
        matching_ids = [
            row.id
            for row in result.scalars().all()
            if all(str(row.changes.get(key)) == str(value) for key, value in filters.items())
        ]
        if matching_ids:
            await session.execute(delete(AuditLog).where(AuditLog.id.in_(matching_ids)))
            await session.commit()


async def delete_tenant(tenant_id: uuid.UUID) -> None:
    async with TestSessionLocal() as session:
        tenant_feature_ids = (
            (
                await session.execute(
                    select(TenantFeature.id).where(TenantFeature.tenant_id == tenant_id)
                )
            )
            .scalars()
            .all()
        )
        await session.execute(delete(TenantFeature).where(TenantFeature.tenant_id == tenant_id))
        await session.execute(delete(Tenant).where(Tenant.id == tenant_id))
        await session.execute(
            delete(AuditLog).where(AuditLog.entity_id.in_([tenant_id, *tenant_feature_ids]))
        )
        await session.commit()


async def delete_feature(feature_id: uuid.UUID) -> None:
    async with TestSessionLocal() as session:
        template_ids = (
            (
                await session.execute(
                    select(OrganizationTypeFeatureTemplate.id).where(
                        OrganizationTypeFeatureTemplate.feature_id == feature_id
                    )
                )
            )
            .scalars()
            .all()
        )
        await session.execute(delete(TenantFeature).where(TenantFeature.feature_id == feature_id))
        await session.execute(
            delete(OrganizationTypeFeatureTemplate).where(
                OrganizationTypeFeatureTemplate.feature_id == feature_id
            )
        )
        await session.execute(delete(Feature).where(Feature.id == feature_id))
        await session.execute(
            delete(AuditLog).where(AuditLog.entity_id.in_([feature_id, *template_ids]))
        )
        await session.commit()


async def delete_organization_type(organization_type_id: uuid.UUID) -> None:
    async with TestSessionLocal() as session:
        template_ids = (
            (
                await session.execute(
                    select(OrganizationTypeFeatureTemplate.id).where(
                        OrganizationTypeFeatureTemplate.organization_type_id == organization_type_id
                    )
                )
            )
            .scalars()
            .all()
        )
        await session.execute(
            delete(OrganizationTypeFeatureTemplate).where(
                OrganizationTypeFeatureTemplate.organization_type_id == organization_type_id
            )
        )
        await session.execute(
            delete(OrganizationType).where(OrganizationType.id == organization_type_id)
        )
        await session.execute(
            delete(AuditLog).where(AuditLog.entity_id.in_([organization_type_id, *template_ids]))
        )
        await session.commit()


async def delete_organization_category(organization_category_id: uuid.UUID) -> None:
    async with TestSessionLocal() as session:
        await session.execute(
            delete(OrganizationCategory).where(OrganizationCategory.id == organization_category_id)
        )
        await session.execute(
            delete(AuditLog).where(AuditLog.entity_id == organization_category_id)
        )
        await session.commit()


# geo cleanup helpers rely on the same append-in-creation-order/LIFO-teardown
# convention as the rest of `cleanup`: append country, then state, then
# district, then city, then tenant - so by the time each of these runs,
# anything that referenced it (created afterward) has already been deleted.
async def delete_country(country_id: uuid.UUID) -> None:
    async with TestSessionLocal() as session:
        await session.execute(delete(Country).where(Country.id == country_id))
        await session.execute(delete(AuditLog).where(AuditLog.entity_id == country_id))
        await session.commit()


async def delete_state(state_id: uuid.UUID) -> None:
    async with TestSessionLocal() as session:
        await session.execute(delete(State).where(State.id == state_id))
        await session.execute(delete(AuditLog).where(AuditLog.entity_id == state_id))
        await session.commit()


async def delete_district(district_id: uuid.UUID) -> None:
    async with TestSessionLocal() as session:
        await session.execute(delete(District).where(District.id == district_id))
        await session.execute(delete(AuditLog).where(AuditLog.entity_id == district_id))
        await session.commit()


async def delete_city(city_id: uuid.UUID) -> None:
    async with TestSessionLocal() as session:
        await session.execute(delete(City).where(City.id == city_id))
        await session.execute(delete(AuditLog).where(AuditLog.entity_id == city_id))
        await session.commit()
