import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.department.models import Department


class DepartmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, department_id: uuid.UUID) -> Department | None:
        result = await self._session.execute(
            select(Department).where(Department.id == department_id)
        )
        return result.scalar_one_or_none()

    async def list_for_tenant(self, tenant_id: uuid.UUID) -> list[Department]:
        result = await self._session.execute(
            select(Department).where(Department.tenant_id == tenant_id).order_by(Department.name)
        )
        return list(result.scalars().all())

    async def create(
        self, *, tenant_id: uuid.UUID, name: str, description: str | None
    ) -> Department:
        department = Department(tenant_id=tenant_id, name=name, description=description)
        self._session.add(department)
        await self._session.commit()
        await self._session.refresh(department)
        return department

    async def update(self, department: Department, **fields: object) -> Department:
        for field_name, value in fields.items():
            setattr(department, field_name, value)
        await self._session.commit()
        await self._session.refresh(department)
        return department

    async def delete(self, department: Department) -> None:
        await self._session.delete(department)
        await self._session.commit()
