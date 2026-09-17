import uuid

from app.domains.location.models import Location
from app.domains.location.repository import LocationRepository


class LocationNotFoundError(Exception):
    pass


async def create_location(
    repository: LocationRepository, *, tenant_id: uuid.UUID, name: str, address: str | None
) -> Location:
    return await repository.create(tenant_id=tenant_id, name=name, address=address)


async def list_locations(repository: LocationRepository, *, tenant_id: uuid.UUID) -> list[Location]:
    return await repository.list_for_tenant(tenant_id)


async def update_location(
    repository: LocationRepository,
    *,
    tenant_id: uuid.UUID,
    location_id: uuid.UUID,
    **fields: object,
) -> Location:
    location = await repository.get_by_id(location_id)
    if location is None or location.tenant_id != tenant_id:
        raise LocationNotFoundError
    return await repository.update(location, **fields)


async def delete_location(
    repository: LocationRepository, *, tenant_id: uuid.UUID, location_id: uuid.UUID
) -> None:
    location = await repository.get_by_id(location_id)
    if location is None or location.tenant_id != tenant_id:
        raise LocationNotFoundError
    await repository.delete(location)
