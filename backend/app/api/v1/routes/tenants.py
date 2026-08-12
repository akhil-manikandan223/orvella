import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import DbSessionDep, get_current_platform_admin
from app.core.slugs import InvalidSlugError
from app.domains.feature.models import Feature
from app.domains.feature.repository import FeatureRepository
from app.domains.feature.schemas import FeatureRead
from app.domains.feature.service import FeatureNotFoundError
from app.domains.geo.service import CityNotFoundError, CountryNotFoundError
from app.domains.organization_taxonomy.service import OrganizationTypeNotFoundError
from app.domains.tenant.models import Tenant
from app.domains.tenant.repository import TenantFeatureRepository, TenantRepository
from app.domains.tenant.schemas import (
    TenantCreate,
    TenantDetailRead,
    TenantFeatureRead,
    TenantFeatureToggleRequest,
    TenantRead,
    TenantUpdate,
)
from app.domains.tenant.service import (
    TenantNotFoundError,
    create_tenant,
    get_tenant_with_features,
    list_tenants,
    set_tenant_feature_enabled,
    update_tenant,
)

router = APIRouter(
    prefix='/platform-admin/tenants',
    tags=['tenants'],
    dependencies=[Depends(get_current_platform_admin)],
)


def _to_detail_read(tenant: Tenant, features: list[Feature]) -> TenantDetailRead:
    return TenantDetailRead(
        **TenantRead.model_validate(tenant).model_dump(),
        features=[FeatureRead.model_validate(feature) for feature in features],
    )


@router.post('', response_model=TenantDetailRead, status_code=status.HTTP_201_CREATED)
async def create_tenant_endpoint(payload: TenantCreate, db: DbSessionDep) -> TenantDetailRead:
    try:
        tenant, features = await create_tenant(db, **payload.model_dump())
    except InvalidSlugError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    except OrganizationTypeNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Organization type not found') from exc
    except CountryNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Country not found') from exc
    except CityNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'City not found') from exc
    return _to_detail_read(tenant, features)


@router.get('', response_model=list[TenantRead])
async def list_tenants_endpoint(db: DbSessionDep) -> list[TenantRead]:
    repository = TenantRepository(db)
    tenants = await list_tenants(repository)
    return [TenantRead.model_validate(tenant) for tenant in tenants]


@router.get('/{tenant_id}', response_model=TenantDetailRead)
async def get_tenant_endpoint(tenant_id: uuid.UUID, db: DbSessionDep) -> TenantDetailRead:
    tenant_repository = TenantRepository(db)
    tenant_feature_repository = TenantFeatureRepository(db)
    feature_repository = FeatureRepository(db)
    try:
        tenant, features = await get_tenant_with_features(
            tenant_repository, tenant_feature_repository, feature_repository, tenant_id=tenant_id
        )
    except TenantNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Tenant not found') from exc
    return _to_detail_read(tenant, features)


@router.patch('/{tenant_id}', response_model=TenantRead)
async def update_tenant_endpoint(
    tenant_id: uuid.UUID, payload: TenantUpdate, db: DbSessionDep
) -> TenantRead:
    repository = TenantRepository(db)
    tenant = await repository.get_by_id(tenant_id)
    if tenant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Tenant not found')
    updated = await update_tenant(repository, tenant, **payload.model_dump(exclude_unset=True))
    return TenantRead.model_validate(updated)


@router.patch('/{tenant_id}/features/{feature_id}', response_model=TenantFeatureRead)
async def toggle_tenant_feature_endpoint(
    tenant_id: uuid.UUID,
    feature_id: uuid.UUID,
    payload: TenantFeatureToggleRequest,
    db: DbSessionDep,
) -> TenantFeatureRead:
    tenant_repository = TenantRepository(db)
    feature_repository = FeatureRepository(db)
    tenant_feature_repository = TenantFeatureRepository(db)
    try:
        tenant_feature = await set_tenant_feature_enabled(
            tenant_repository,
            feature_repository,
            tenant_feature_repository,
            tenant_id=tenant_id,
            feature_id=feature_id,
            enabled=payload.enabled,
        )
    except TenantNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Tenant not found') from exc
    except FeatureNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Feature not found') from exc
    return TenantFeatureRead.model_validate(tenant_feature)
