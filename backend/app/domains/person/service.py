import uuid

from app.domains.department.repository import DepartmentRepository
from app.domains.location.repository import LocationRepository
from app.domains.person.models import Person
from app.domains.person.repository import PersonRepository


class PersonNotFoundError(Exception):
    pass


class DepartmentNotInTenantError(Exception):
    pass


class LocationNotInTenantError(Exception):
    pass


async def _validate_department_and_location(
    department_repository: DepartmentRepository,
    location_repository: LocationRepository,
    *,
    tenant_id: uuid.UUID,
    department_id: uuid.UUID | None,
    location_id: uuid.UUID | None,
) -> None:
    """A department_id/location_id that exists but belongs to a *different*
    tenant must be rejected here - the foreign key alone only guarantees the
    row exists somewhere, not that it's this tenant's own.
    """
    if department_id is not None:
        department = await department_repository.get_by_id(department_id)
        if department is None or department.tenant_id != tenant_id:
            raise DepartmentNotInTenantError
    if location_id is not None:
        location = await location_repository.get_by_id(location_id)
        if location is None or location.tenant_id != tenant_id:
            raise LocationNotInTenantError


async def create_person(
    person_repository: PersonRepository,
    department_repository: DepartmentRepository,
    location_repository: LocationRepository,
    *,
    tenant_id: uuid.UUID,
    first_name: str,
    last_name: str,
    category: str,
    email: str | None,
    phone: str | None,
    department_id: uuid.UUID | None,
    location_id: uuid.UUID | None,
) -> Person:
    await _validate_department_and_location(
        department_repository,
        location_repository,
        tenant_id=tenant_id,
        department_id=department_id,
        location_id=location_id,
    )
    return await person_repository.create(
        tenant_id=tenant_id,
        first_name=first_name,
        last_name=last_name,
        category=category,
        email=email,
        phone=phone,
        department_id=department_id,
        location_id=location_id,
    )


async def list_people(person_repository: PersonRepository, *, tenant_id: uuid.UUID) -> list[Person]:
    return await person_repository.list_for_tenant(tenant_id)


async def update_person(
    person_repository: PersonRepository,
    department_repository: DepartmentRepository,
    location_repository: LocationRepository,
    *,
    tenant_id: uuid.UUID,
    person_id: uuid.UUID,
    **fields: object,
) -> Person:
    person = await person_repository.get_by_id(person_id)
    if person is None or person.tenant_id != tenant_id:
        raise PersonNotFoundError
    if 'department_id' in fields or 'location_id' in fields:
        await _validate_department_and_location(
            department_repository,
            location_repository,
            tenant_id=tenant_id,
            department_id=fields.get('department_id', person.department_id),  # type: ignore[arg-type]
            location_id=fields.get('location_id', person.location_id),  # type: ignore[arg-type]
        )
    return await person_repository.update(person, **fields)


async def delete_person(
    person_repository: PersonRepository, *, tenant_id: uuid.UUID, person_id: uuid.UUID
) -> None:
    person = await person_repository.get_by_id(person_id)
    if person is None or person.tenant_id != tenant_id:
        raise PersonNotFoundError
    await person_repository.delete(person)
