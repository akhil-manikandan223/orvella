import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import CurrentTenantDep, DbSessionDep, require_tenant_permission
from app.domains.location.repository import LocationRepository
from app.domains.location.schemas import LocationCreate, LocationRead, LocationUpdate
from app.domains.location.service import (
    LocationNotFoundError,
    create_location,
    delete_location,
    list_locations,
    update_location,
)
from app.domains.tenant_user.permissions import TenantPermission

router = APIRouter(prefix='/tenant/locations', tags=['tenant-locations'])


@router.get(
    '',
    response_model=list[LocationRead],
    dependencies=[Depends(require_tenant_permission(TenantPermission.LOCATIONS_VIEW))],
)
async def list_locations_endpoint(tenant: CurrentTenantDep, db: DbSessionDep) -> list[LocationRead]:
    repository = LocationRepository(db)
    locations = await list_locations(repository, tenant_id=tenant.id)
    return [LocationRead.model_validate(location) for location in locations]


@router.post(
    '',
    response_model=LocationRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_tenant_permission(TenantPermission.LOCATIONS_MANAGE))],
)
async def create_location_endpoint(
    payload: LocationCreate, tenant: CurrentTenantDep, db: DbSessionDep
) -> LocationRead:
    repository = LocationRepository(db)
    location = await create_location(
        repository, tenant_id=tenant.id, name=payload.name, address=payload.address
    )
    return LocationRead.model_validate(location)


@router.patch(
    '/{location_id}',
    response_model=LocationRead,
    dependencies=[Depends(require_tenant_permission(TenantPermission.LOCATIONS_MANAGE))],
)
async def update_location_endpoint(
    location_id: uuid.UUID,
    payload: LocationUpdate,
    tenant: CurrentTenantDep,
    db: DbSessionDep,
) -> LocationRead:
    repository = LocationRepository(db)
    try:
        location = await update_location(
            repository,
            tenant_id=tenant.id,
            location_id=location_id,
            **payload.model_dump(exclude_unset=True),
        )
    except LocationNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Location not found') from exc
    return LocationRead.model_validate(location)


@router.delete(
    '/{location_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_tenant_permission(TenantPermission.LOCATIONS_MANAGE))],
)
async def delete_location_endpoint(
    location_id: uuid.UUID, tenant: CurrentTenantDep, db: DbSessionDep
) -> None:
    repository = LocationRepository(db)
    try:
        await delete_location(repository, tenant_id=tenant.id, location_id=location_id)
    except LocationNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Location not found') from exc
