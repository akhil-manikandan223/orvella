import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import DbSessionDep, get_current_platform_admin
from app.core.slugs import InvalidSlugError
from app.domains.geo.repository import CityRepository, DistrictRepository, StateRepository
from app.domains.geo.schemas import CityCreate, CityRead, CityUpdate
from app.domains.geo.service import (
    CityNotFoundError,
    DistrictNotFoundError,
    StateNotFoundError,
    create_city,
    list_cities,
    update_city,
)

router = APIRouter(
    prefix='/platform-admin/cities',
    tags=['geo'],
    dependencies=[Depends(get_current_platform_admin)],
)


@router.post('', response_model=CityRead, status_code=status.HTTP_201_CREATED)
async def create_city_endpoint(payload: CityCreate, db: DbSessionDep) -> CityRead:
    city_repository = CityRepository(db)
    state_repository = StateRepository(db)
    district_repository = DistrictRepository(db)
    try:
        city = await create_city(
            city_repository,
            state_repository,
            district_repository,
            state_id=payload.state_id,
            district_id=payload.district_id,
            name=payload.name,
            slug=payload.slug,
        )
    except StateNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'State not found') from exc
    except DistrictNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'District not found') from exc
    return CityRead.model_validate(city)


@router.get('', response_model=list[CityRead])
async def list_cities_endpoint(
    db: DbSessionDep,
    state_id: uuid.UUID | None = None,
    district_id: uuid.UUID | None = None,
) -> list[CityRead]:
    repository = CityRepository(db)
    cities = await list_cities(repository, state_id=state_id, district_id=district_id)
    return [CityRead.model_validate(city) for city in cities]


@router.patch('/{city_id}', response_model=CityRead)
async def update_city_endpoint(
    city_id: uuid.UUID, payload: CityUpdate, db: DbSessionDep
) -> CityRead:
    repository = CityRepository(db)
    try:
        city = await update_city(repository, city_id, **payload.model_dump(exclude_unset=True))
    except CityNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'City not found') from exc
    except InvalidSlugError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    return CityRead.model_validate(city)
