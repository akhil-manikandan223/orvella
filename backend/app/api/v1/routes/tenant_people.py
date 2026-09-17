import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import CurrentTenantDep, DbSessionDep, require_tenant_permission
from app.domains.department.repository import DepartmentRepository
from app.domains.location.repository import LocationRepository
from app.domains.person.repository import PersonRepository
from app.domains.person.schemas import PersonCreate, PersonRead, PersonUpdate
from app.domains.person.service import (
    DepartmentNotInTenantError,
    LocationNotInTenantError,
    PersonNotFoundError,
    create_person,
    delete_person,
    list_people,
    update_person,
)
from app.domains.tenant_user.permissions import TenantPermission

router = APIRouter(prefix='/tenant/people', tags=['tenant-people'])


@router.get(
    '',
    response_model=list[PersonRead],
    dependencies=[Depends(require_tenant_permission(TenantPermission.PEOPLE_VIEW))],
)
async def list_people_endpoint(tenant: CurrentTenantDep, db: DbSessionDep) -> list[PersonRead]:
    repository = PersonRepository(db)
    people = await list_people(repository, tenant_id=tenant.id)
    return [PersonRead.model_validate(person) for person in people]


@router.post(
    '',
    response_model=PersonRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_tenant_permission(TenantPermission.PEOPLE_MANAGE))],
)
async def create_person_endpoint(
    payload: PersonCreate, tenant: CurrentTenantDep, db: DbSessionDep
) -> PersonRead:
    person_repository = PersonRepository(db)
    department_repository = DepartmentRepository(db)
    location_repository = LocationRepository(db)
    try:
        person = await create_person(
            person_repository,
            department_repository,
            location_repository,
            tenant_id=tenant.id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            category=payload.category,
            email=payload.email,
            phone=payload.phone,
            department_id=payload.department_id,
            location_id=payload.location_id,
        )
    except DepartmentNotInTenantError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, 'Department not found for this tenant'
        ) from exc
    except LocationNotInTenantError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, 'Location not found for this tenant'
        ) from exc
    return PersonRead.model_validate(person)


@router.patch(
    '/{person_id}',
    response_model=PersonRead,
    dependencies=[Depends(require_tenant_permission(TenantPermission.PEOPLE_MANAGE))],
)
async def update_person_endpoint(
    person_id: uuid.UUID, payload: PersonUpdate, tenant: CurrentTenantDep, db: DbSessionDep
) -> PersonRead:
    person_repository = PersonRepository(db)
    department_repository = DepartmentRepository(db)
    location_repository = LocationRepository(db)
    try:
        person = await update_person(
            person_repository,
            department_repository,
            location_repository,
            tenant_id=tenant.id,
            person_id=person_id,
            **payload.model_dump(exclude_unset=True),
        )
    except PersonNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Person not found') from exc
    except DepartmentNotInTenantError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, 'Department not found for this tenant'
        ) from exc
    except LocationNotInTenantError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, 'Location not found for this tenant'
        ) from exc
    return PersonRead.model_validate(person)


@router.delete(
    '/{person_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_tenant_permission(TenantPermission.PEOPLE_MANAGE))],
)
async def delete_person_endpoint(
    person_id: uuid.UUID, tenant: CurrentTenantDep, db: DbSessionDep
) -> None:
    repository = PersonRepository(db)
    try:
        await delete_person(repository, tenant_id=tenant.id, person_id=person_id)
    except PersonNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Person not found') from exc
