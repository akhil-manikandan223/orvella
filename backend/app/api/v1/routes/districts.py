import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import DbSessionDep, get_current_platform_admin
from app.core.slugs import InvalidSlugError
from app.domains.geo.repository import DistrictRepository, StateRepository
from app.domains.geo.schemas import DistrictCreate, DistrictRead, DistrictUpdate
from app.domains.geo.service import (
    DistrictNotFoundError,
    StateNotFoundError,
    create_district,
    list_districts,
    update_district,
)

router = APIRouter(
    prefix='/platform-admin/districts',
    tags=['geo'],
    dependencies=[Depends(get_current_platform_admin)],
)


@router.post('', response_model=DistrictRead, status_code=status.HTTP_201_CREATED)
async def create_district_endpoint(payload: DistrictCreate, db: DbSessionDep) -> DistrictRead:
    district_repository = DistrictRepository(db)
    state_repository = StateRepository(db)
    try:
        district = await create_district(
            district_repository,
            state_repository,
            state_id=payload.state_id,
            name=payload.name,
            slug=payload.slug,
        )
    except StateNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'State not found') from exc
    return DistrictRead.model_validate(district)


@router.get('', response_model=list[DistrictRead])
async def list_districts_endpoint(
    db: DbSessionDep, state_id: uuid.UUID | None = None
) -> list[DistrictRead]:
    repository = DistrictRepository(db)
    districts = await list_districts(repository, state_id=state_id)
    return [DistrictRead.model_validate(district) for district in districts]


@router.patch('/{district_id}', response_model=DistrictRead)
async def update_district_endpoint(
    district_id: uuid.UUID, payload: DistrictUpdate, db: DbSessionDep
) -> DistrictRead:
    repository = DistrictRepository(db)
    try:
        district = await update_district(
            repository, district_id, **payload.model_dump(exclude_unset=True)
        )
    except DistrictNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'District not found') from exc
    except InvalidSlugError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    return DistrictRead.model_validate(district)
