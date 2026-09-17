import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.location.models import Location


class LocationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, location_id: uuid.UUID) -> Location | None:
        result = await self._session.execute(select(Location).where(Location.id == location_id))
        return result.scalar_one_or_none()

    async def list_for_tenant(self, tenant_id: uuid.UUID) -> list[Location]:
        result = await self._session.execute(
            select(Location).where(Location.tenant_id == tenant_id).order_by(Location.name)
        )
        return list(result.scalars().all())

    async def create(self, *, tenant_id: uuid.UUID, name: str, address: str | None) -> Location:
        location = Location(tenant_id=tenant_id, name=name, address=address)
        self._session.add(location)
        await self._session.commit()
        await self._session.refresh(location)
        return location

    async def update(self, location: Location, **fields: object) -> Location:
        for field_name, value in fields.items():
            setattr(location, field_name, value)
        await self._session.commit()
        await self._session.refresh(location)
        return location

    async def delete(self, location: Location) -> None:
        await self._session.delete(location)
        await self._session.commit()
