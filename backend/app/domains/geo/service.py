import uuid

from app.core.slugs import MAX_TAXONOMY_SLUG_LENGTH, validate_slug_format
from app.domains.geo.models import City, Country, District, State
from app.domains.geo.repository import (
    CityRepository,
    CountryRepository,
    DistrictRepository,
    StateRepository,
)


class CountryNotFoundError(Exception):
    pass


class StateNotFoundError(Exception):
    pass


class DistrictNotFoundError(Exception):
    pass


class CityNotFoundError(Exception):
    pass


async def create_country(repository: CountryRepository, *, name: str, slug: str) -> Country:
    validate_slug_format(slug, max_length=MAX_TAXONOMY_SLUG_LENGTH)
    return await repository.create(name=name, slug=slug)


async def list_countries(repository: CountryRepository) -> list[Country]:
    return await repository.list_all()


async def update_country(
    repository: CountryRepository, country_id: uuid.UUID, **fields: object
) -> Country:
    country = await repository.get_by_id(country_id)
    if country is None:
        raise CountryNotFoundError
    if fields.get('slug') is not None:
        validate_slug_format(fields['slug'], max_length=MAX_TAXONOMY_SLUG_LENGTH)
    return await repository.update(country, **fields)


async def create_state(
    state_repository: StateRepository,
    country_repository: CountryRepository,
    *,
    country_id: uuid.UUID,
    name: str,
    slug: str,
) -> State:
    validate_slug_format(slug, max_length=MAX_TAXONOMY_SLUG_LENGTH)
    if await country_repository.get_by_id(country_id) is None:
        raise CountryNotFoundError
    return await state_repository.create(country_id=country_id, name=name, slug=slug)


async def list_states(repository: StateRepository, *, country_id: uuid.UUID | None) -> list[State]:
    return await repository.list_all(country_id=country_id)


async def update_state(repository: StateRepository, state_id: uuid.UUID, **fields: object) -> State:
    state = await repository.get_by_id(state_id)
    if state is None:
        raise StateNotFoundError
    if fields.get('slug') is not None:
        validate_slug_format(fields['slug'], max_length=MAX_TAXONOMY_SLUG_LENGTH)
    return await repository.update(state, **fields)


async def create_district(
    district_repository: DistrictRepository,
    state_repository: StateRepository,
    *,
    state_id: uuid.UUID,
    name: str,
    slug: str,
) -> District:
    validate_slug_format(slug, max_length=MAX_TAXONOMY_SLUG_LENGTH)
    if await state_repository.get_by_id(state_id) is None:
        raise StateNotFoundError
    return await district_repository.create(state_id=state_id, name=name, slug=slug)


async def list_districts(
    repository: DistrictRepository, *, state_id: uuid.UUID | None
) -> list[District]:
    return await repository.list_all(state_id=state_id)


async def update_district(
    repository: DistrictRepository, district_id: uuid.UUID, **fields: object
) -> District:
    district = await repository.get_by_id(district_id)
    if district is None:
        raise DistrictNotFoundError
    if fields.get('slug') is not None:
        validate_slug_format(fields['slug'], max_length=MAX_TAXONOMY_SLUG_LENGTH)
    return await repository.update(district, **fields)


async def create_city(
    city_repository: CityRepository,
    state_repository: StateRepository,
    district_repository: DistrictRepository,
    *,
    state_id: uuid.UUID,
    district_id: uuid.UUID | None,
    name: str,
    slug: str,
) -> City:
    validate_slug_format(slug, max_length=MAX_TAXONOMY_SLUG_LENGTH)
    if await state_repository.get_by_id(state_id) is None:
        raise StateNotFoundError
    if district_id is not None and await district_repository.get_by_id(district_id) is None:
        raise DistrictNotFoundError
    return await city_repository.create(
        state_id=state_id, district_id=district_id, name=name, slug=slug
    )


async def list_cities(
    repository: CityRepository, *, state_id: uuid.UUID | None, district_id: uuid.UUID | None
) -> list[City]:
    return await repository.list_all(state_id=state_id, district_id=district_id)


async def update_city(repository: CityRepository, city_id: uuid.UUID, **fields: object) -> City:
    city = await repository.get_by_id(city_id)
    if city is None:
        raise CityNotFoundError
    if fields.get('slug') is not None:
        validate_slug_format(fields['slug'], max_length=MAX_TAXONOMY_SLUG_LENGTH)
    return await repository.update(city, **fields)
