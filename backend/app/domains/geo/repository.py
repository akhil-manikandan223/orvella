import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.geo.models import City, Country, District, State


class CountryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, country_id: uuid.UUID) -> Country | None:
        result = await self._session.execute(select(Country).where(Country.id == country_id))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Country]:
        result = await self._session.execute(select(Country).order_by(Country.name))
        return list(result.scalars().all())

    async def create(self, *, name: str, slug: str) -> Country:
        country = Country(name=name, slug=slug)
        self._session.add(country)
        await self._session.commit()
        await self._session.refresh(country)
        return country

    async def update(self, country: Country, **fields: object) -> Country:
        for field_name, value in fields.items():
            setattr(country, field_name, value)
        await self._session.commit()
        await self._session.refresh(country)
        return country


class StateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, state_id: uuid.UUID) -> State | None:
        result = await self._session.execute(select(State).where(State.id == state_id))
        return result.scalar_one_or_none()

    async def list_all(self, *, country_id: uuid.UUID | None) -> list[State]:
        query = select(State).order_by(State.name)
        if country_id is not None:
            query = query.where(State.country_id == country_id)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def create(self, *, country_id: uuid.UUID, name: str, slug: str) -> State:
        state = State(country_id=country_id, name=name, slug=slug)
        self._session.add(state)
        await self._session.commit()
        await self._session.refresh(state)
        return state

    async def update(self, state: State, **fields: object) -> State:
        for field_name, value in fields.items():
            setattr(state, field_name, value)
        await self._session.commit()
        await self._session.refresh(state)
        return state


class DistrictRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, district_id: uuid.UUID) -> District | None:
        result = await self._session.execute(select(District).where(District.id == district_id))
        return result.scalar_one_or_none()

    async def list_all(self, *, state_id: uuid.UUID | None) -> list[District]:
        query = select(District).order_by(District.name)
        if state_id is not None:
            query = query.where(District.state_id == state_id)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def create(self, *, state_id: uuid.UUID, name: str, slug: str) -> District:
        district = District(state_id=state_id, name=name, slug=slug)
        self._session.add(district)
        await self._session.commit()
        await self._session.refresh(district)
        return district

    async def update(self, district: District, **fields: object) -> District:
        for field_name, value in fields.items():
            setattr(district, field_name, value)
        await self._session.commit()
        await self._session.refresh(district)
        return district


class CityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, city_id: uuid.UUID) -> City | None:
        result = await self._session.execute(select(City).where(City.id == city_id))
        return result.scalar_one_or_none()

    async def list_all(
        self, *, state_id: uuid.UUID | None, district_id: uuid.UUID | None
    ) -> list[City]:
        query = select(City).order_by(City.name)
        if state_id is not None:
            query = query.where(City.state_id == state_id)
        if district_id is not None:
            query = query.where(City.district_id == district_id)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def create(
        self, *, state_id: uuid.UUID, district_id: uuid.UUID | None, name: str, slug: str
    ) -> City:
        city = City(state_id=state_id, district_id=district_id, name=name, slug=slug)
        self._session.add(city)
        await self._session.commit()
        await self._session.refresh(city)
        return city

    async def update(self, city: City, **fields: object) -> City:
        for field_name, value in fields.items():
            setattr(city, field_name, value)
        await self._session.commit()
        await self._session.refresh(city)
        return city
