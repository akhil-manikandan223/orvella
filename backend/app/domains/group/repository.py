import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.group.models import Group, GroupMember, GroupSupervisor


class GroupRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, group_id: uuid.UUID) -> Group | None:
        result = await self._session.execute(select(Group).where(Group.id == group_id))
        return result.scalar_one_or_none()

    async def list_for_tenant(self, tenant_id: uuid.UUID) -> list[Group]:
        result = await self._session.execute(
            select(Group).where(Group.tenant_id == tenant_id).order_by(Group.name)
        )
        return list(result.scalars().all())

    async def list_for_supervisor(
        self, *, tenant_id: uuid.UUID, tenant_user_id: uuid.UUID
    ) -> list[Group]:
        result = await self._session.execute(
            select(Group)
            .join(GroupSupervisor, GroupSupervisor.group_id == Group.id)
            .where(Group.tenant_id == tenant_id, GroupSupervisor.tenant_user_id == tenant_user_id)
            .order_by(Group.name)
        )
        return list(result.scalars().all())

    async def create(
        self,
        *,
        tenant_id: uuid.UUID,
        name: str,
        description: str | None,
        department_id: uuid.UUID | None,
    ) -> Group:
        group = Group(
            tenant_id=tenant_id, name=name, description=description, department_id=department_id
        )
        self._session.add(group)
        await self._session.commit()
        await self._session.refresh(group)
        return group

    async def update(self, group: Group, **fields: object) -> Group:
        for field_name, value in fields.items():
            setattr(group, field_name, value)
        await self._session.commit()
        await self._session.refresh(group)
        return group

    async def delete(self, group: Group) -> None:
        await self._session.delete(group)
        await self._session.commit()

    # ---- membership ----

    async def list_member_ids(self, group_id: uuid.UUID) -> list[uuid.UUID]:
        result = await self._session.execute(
            select(GroupMember.person_id).where(GroupMember.group_id == group_id)
        )
        return list(result.scalars().all())

    async def list_member_ids_for_groups(self, group_ids: list[uuid.UUID]) -> set[uuid.UUID]:
        if not group_ids:
            return set()
        result = await self._session.execute(
            select(GroupMember.person_id).where(GroupMember.group_id.in_(group_ids))
        )
        return set(result.scalars().all())

    async def replace_members(self, group_id: uuid.UUID, person_ids: list[uuid.UUID]) -> None:
        await self._session.execute(delete(GroupMember).where(GroupMember.group_id == group_id))
        self._session.add_all(
            [GroupMember(group_id=group_id, person_id=person_id) for person_id in set(person_ids)]
        )
        await self._session.commit()

    # ---- supervision ----

    async def list_supervisor_ids(self, group_id: uuid.UUID) -> list[uuid.UUID]:
        result = await self._session.execute(
            select(GroupSupervisor.tenant_user_id).where(GroupSupervisor.group_id == group_id)
        )
        return list(result.scalars().all())

    async def replace_supervisors(
        self, group_id: uuid.UUID, tenant_user_ids: list[uuid.UUID]
    ) -> None:
        await self._session.execute(
            delete(GroupSupervisor).where(GroupSupervisor.group_id == group_id)
        )
        self._session.add_all(
            [
                GroupSupervisor(group_id=group_id, tenant_user_id=user_id)
                for user_id in set(tenant_user_ids)
            ]
        )
        await self._session.commit()
