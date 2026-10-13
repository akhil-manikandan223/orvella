import uuid

from app.domains.group.models import Group
from app.domains.group.repository import GroupRepository
from app.domains.person.repository import PersonRepository
from app.domains.tenant_user.repository import TenantUserRepository


class GroupNotFoundError(Exception):
    pass


class PersonNotInTenantError(Exception):
    pass


class SupervisorNotInTenantError(Exception):
    pass


async def create_group(
    repository: GroupRepository,
    *,
    tenant_id: uuid.UUID,
    name: str,
    description: str | None,
    department_id: uuid.UUID | None,
) -> Group:
    return await repository.create(
        tenant_id=tenant_id, name=name, description=description, department_id=department_id
    )


async def list_groups(repository: GroupRepository, *, tenant_id: uuid.UUID) -> list[Group]:
    return await repository.list_for_tenant(tenant_id)


async def get_group(
    repository: GroupRepository, *, tenant_id: uuid.UUID, group_id: uuid.UUID
) -> Group:
    group = await repository.get_by_id(group_id)
    if group is None or group.tenant_id != tenant_id:
        raise GroupNotFoundError
    return group


async def update_group(
    repository: GroupRepository, *, tenant_id: uuid.UUID, group_id: uuid.UUID, **fields: object
) -> Group:
    group = await get_group(repository, tenant_id=tenant_id, group_id=group_id)
    return await repository.update(group, **fields)


async def delete_group(
    repository: GroupRepository, *, tenant_id: uuid.UUID, group_id: uuid.UUID
) -> None:
    group = await get_group(repository, tenant_id=tenant_id, group_id=group_id)
    await repository.delete(group)


async def set_group_members(
    repository: GroupRepository,
    person_repository: PersonRepository,
    *,
    tenant_id: uuid.UUID,
    group_id: uuid.UUID,
    person_ids: list[uuid.UUID],
) -> list[uuid.UUID]:
    await get_group(repository, tenant_id=tenant_id, group_id=group_id)

    # The group is tenant-scoped but the ids come from the request body, so
    # without this a tenant could pull another tenant's people into a group -
    # and then mark their attendance through it.
    owned = {person.id for person in await person_repository.list_for_tenant(tenant_id)}
    if not set(person_ids) <= owned:
        raise PersonNotInTenantError

    await repository.replace_members(group_id, person_ids)
    return await repository.list_member_ids(group_id)


async def set_group_supervisors(
    repository: GroupRepository,
    tenant_user_repository: TenantUserRepository,
    *,
    tenant_id: uuid.UUID,
    group_id: uuid.UUID,
    tenant_user_ids: list[uuid.UUID],
) -> list[uuid.UUID]:
    await get_group(repository, tenant_id=tenant_id, group_id=group_id)

    owned = {user.id for user in await tenant_user_repository.list_for_tenant(tenant_id)}
    if not set(tenant_user_ids) <= owned:
        raise SupervisorNotInTenantError

    await repository.replace_supervisors(group_id, tenant_user_ids)
    return await repository.list_supervisor_ids(group_id)


async def list_supervised_person_ids(
    repository: GroupRepository, *, tenant_id: uuid.UUID, tenant_user_id: uuid.UUID
) -> set[uuid.UUID]:
    """Everyone this user is responsible for, via the groups they supervise.

    This is the attendance scope for a non-admin: a homeroom teacher sees and
    marks their own classes and nothing else. Returns an empty set when they
    supervise nothing, which correctly means "no roster" rather than "all".
    """
    groups = await repository.list_for_supervisor(
        tenant_id=tenant_id, tenant_user_id=tenant_user_id
    )
    return await repository.list_member_ids_for_groups([group.id for group in groups])
