import uuid

from app.domains.department.models import Department
from app.domains.department.repository import DepartmentRepository


class DepartmentNotFoundError(Exception):
    pass


async def create_department(
    repository: DepartmentRepository,
    *,
    tenant_id: uuid.UUID,
    name: str,
    description: str | None,
) -> Department:
    return await repository.create(tenant_id=tenant_id, name=name, description=description)


async def list_departments(
    repository: DepartmentRepository, *, tenant_id: uuid.UUID
) -> list[Department]:
    return await repository.list_for_tenant(tenant_id)


async def update_department(
    repository: DepartmentRepository,
    *,
    tenant_id: uuid.UUID,
    department_id: uuid.UUID,
    **fields: object,
) -> Department:
    department = await repository.get_by_id(department_id)
    if department is None or department.tenant_id != tenant_id:
        raise DepartmentNotFoundError
    return await repository.update(department, **fields)


async def delete_department(
    repository: DepartmentRepository, *, tenant_id: uuid.UUID, department_id: uuid.UUID
) -> None:
    department = await repository.get_by_id(department_id)
    if department is None or department.tenant_id != tenant_id:
        raise DepartmentNotFoundError
    await repository.delete(department)
