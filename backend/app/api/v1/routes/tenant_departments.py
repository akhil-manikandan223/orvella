import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import CurrentTenantDep, DbSessionDep, require_tenant_permission
from app.domains.department.repository import DepartmentRepository
from app.domains.department.schemas import DepartmentCreate, DepartmentRead, DepartmentUpdate
from app.domains.department.service import (
    DepartmentNotFoundError,
    create_department,
    delete_department,
    list_departments,
    update_department,
)
from app.domains.tenant_user.permissions import TenantPermission

router = APIRouter(prefix='/tenant/departments', tags=['tenant-departments'])


@router.get(
    '',
    response_model=list[DepartmentRead],
    dependencies=[Depends(require_tenant_permission(TenantPermission.DEPARTMENTS_VIEW))],
)
async def list_departments_endpoint(
    tenant: CurrentTenantDep, db: DbSessionDep
) -> list[DepartmentRead]:
    repository = DepartmentRepository(db)
    departments = await list_departments(repository, tenant_id=tenant.id)
    return [DepartmentRead.model_validate(d) for d in departments]


@router.post(
    '',
    response_model=DepartmentRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_tenant_permission(TenantPermission.DEPARTMENTS_MANAGE))],
)
async def create_department_endpoint(
    payload: DepartmentCreate, tenant: CurrentTenantDep, db: DbSessionDep
) -> DepartmentRead:
    repository = DepartmentRepository(db)
    department = await create_department(
        repository, tenant_id=tenant.id, name=payload.name, description=payload.description
    )
    return DepartmentRead.model_validate(department)


@router.patch(
    '/{department_id}',
    response_model=DepartmentRead,
    dependencies=[Depends(require_tenant_permission(TenantPermission.DEPARTMENTS_MANAGE))],
)
async def update_department_endpoint(
    department_id: uuid.UUID,
    payload: DepartmentUpdate,
    tenant: CurrentTenantDep,
    db: DbSessionDep,
) -> DepartmentRead:
    repository = DepartmentRepository(db)
    try:
        department = await update_department(
            repository,
            tenant_id=tenant.id,
            department_id=department_id,
            **payload.model_dump(exclude_unset=True),
        )
    except DepartmentNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Department not found') from exc
    return DepartmentRead.model_validate(department)


@router.delete(
    '/{department_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_tenant_permission(TenantPermission.DEPARTMENTS_MANAGE))],
)
async def delete_department_endpoint(
    department_id: uuid.UUID, tenant: CurrentTenantDep, db: DbSessionDep
) -> None:
    repository = DepartmentRepository(db)
    try:
        await delete_department(repository, tenant_id=tenant.id, department_id=department_id)
    except DepartmentNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Department not found') from exc
