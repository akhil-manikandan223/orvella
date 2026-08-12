import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import DbSessionDep, get_current_platform_admin
from app.core.slugs import InvalidSlugError
from app.domains.geo.repository import CountryRepository
from app.domains.geo.schemas import CountryCreate, CountryRead, CountryUpdate
from app.domains.geo.service import (
    CountryNotFoundError,
    create_country,
    list_countries,
    update_country,
)

router = APIRouter(
    prefix='/platform-admin/countries',
    tags=['geo'],
    dependencies=[Depends(get_current_platform_admin)],
)


@router.post('', response_model=CountryRead, status_code=status.HTTP_201_CREATED)
async def create_country_endpoint(payload: CountryCreate, db: DbSessionDep) -> CountryRead:
    repository = CountryRepository(db)
    country = await create_country(repository, name=payload.name, slug=payload.slug)
    return CountryRead.model_validate(country)


@router.get('', response_model=list[CountryRead])
async def list_countries_endpoint(db: DbSessionDep) -> list[CountryRead]:
    repository = CountryRepository(db)
    countries = await list_countries(repository)
    return [CountryRead.model_validate(country) for country in countries]


@router.patch('/{country_id}', response_model=CountryRead)
async def update_country_endpoint(
    country_id: uuid.UUID, payload: CountryUpdate, db: DbSessionDep
) -> CountryRead:
    repository = CountryRepository(db)
    try:
        country = await update_country(
            repository, country_id, **payload.model_dump(exclude_unset=True)
        )
    except CountryNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Country not found') from exc
    except InvalidSlugError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    return CountryRead.model_validate(country)
