import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import (
    CurrentTenantDep,
    CurrentTenantUserDep,
    DbSessionDep,
    require_tenant_permission,
)
from app.domains.group.repository import GroupRepository
from app.domains.group.schemas import (
    GroupCreate,
    GroupDetailRead,
    GroupMembersUpdate,
    GroupRead,
    GroupSupervisorsUpdate,
    GroupUpdate,
)
from app.domains.group.service import (
    GroupNotFoundError,
    PersonNotInTenantError,
    SupervisorNotInTenantError,
    create_group,
    delete_group,
    get_group,
    list_groups,
    set_group_members,
    set_group_supervisors,
    update_group,
)
from app.domains.person.repository import PersonRepository
from app.domains.tenant_user.permissions import TenantPermission
from app.domains.tenant_user.repository import TenantUserRepository

router = APIRouter(prefix='/tenant/groups', tags=['tenant-groups'])


async def _load_detail(
    repository: GroupRepository, *, tenant_id: uuid.UUID, group_id: uuid.UUID
) -> GroupDetailRead:
    group = await get_group(repository, tenant_id=tenant_id, group_id=group_id)
    return GroupDetailRead(
        **GroupRead.model_validate(group).model_dump(),
        member_ids=await repository.list_member_ids(group.id),
        supervisor_ids=await repository.list_supervisor_ids(group.id),
    )


@router.get(
    '',
    response_model=list[GroupRead],
    dependencies=[Depends(require_tenant_permission(TenantPermission.GROUPS_VIEW))],
)
async def list_groups_endpoint(tenant: CurrentTenantDep, db: DbSessionDep) -> list[GroupRead]:
    groups = await list_groups(GroupRepository(db), tenant_id=tenant.id)
    return [GroupRead.model_validate(group) for group in groups]


@router.get(
    '/supervised',
    response_model=list[GroupDetailRead],
    dependencies=[Depends(require_tenant_permission(TenantPermission.GROUPS_VIEW))],
)
async def list_supervised_groups_endpoint(
    tenant: CurrentTenantDep, db: DbSessionDep, user: CurrentTenantUserDep
) -> list[GroupDetailRead]:
    """The groups the caller personally supervises, with their rosters.

    What a homeroom teacher's attendance screen is built from. Declared
    before /{group_id} so 'supervised' isn't parsed as a UUID path param.
    """
    repository = GroupRepository(db)
    groups = await repository.list_for_supervisor(tenant_id=tenant.id, tenant_user_id=user.id)
    return [
        await _load_detail(repository, tenant_id=tenant.id, group_id=group.id) for group in groups
    ]


@router.get(
    '/{group_id}',
    response_model=GroupDetailRead,
    dependencies=[Depends(require_tenant_permission(TenantPermission.GROUPS_VIEW))],
)
async def get_group_endpoint(
    group_id: uuid.UUID, tenant: CurrentTenantDep, db: DbSessionDep
) -> GroupDetailRead:
    try:
        return await _load_detail(GroupRepository(db), tenant_id=tenant.id, group_id=group_id)
    except GroupNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Group not found') from exc


@router.post(
    '',
    response_model=GroupRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_tenant_permission(TenantPermission.GROUPS_MANAGE))],
)
async def create_group_endpoint(
    payload: GroupCreate, tenant: CurrentTenantDep, db: DbSessionDep
) -> GroupRead:
    group = await create_group(
        GroupRepository(db),
        tenant_id=tenant.id,
        name=payload.name,
        description=payload.description,
        department_id=payload.department_id,
    )
    return GroupRead.model_validate(group)


@router.patch(
    '/{group_id}',
    response_model=GroupRead,
    dependencies=[Depends(require_tenant_permission(TenantPermission.GROUPS_MANAGE))],
)
async def update_group_endpoint(
    group_id: uuid.UUID, payload: GroupUpdate, tenant: CurrentTenantDep, db: DbSessionDep
) -> GroupRead:
    try:
        group = await update_group(
            GroupRepository(db),
            tenant_id=tenant.id,
            group_id=group_id,
            **payload.model_dump(exclude_unset=True),
        )
    except GroupNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Group not found') from exc
    return GroupRead.model_validate(group)


@router.delete(
    '/{group_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_tenant_permission(TenantPermission.GROUPS_MANAGE))],
)
async def delete_group_endpoint(
    group_id: uuid.UUID, tenant: CurrentTenantDep, db: DbSessionDep
) -> None:
    try:
        await delete_group(GroupRepository(db), tenant_id=tenant.id, group_id=group_id)
    except GroupNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Group not found') from exc


@router.put(
    '/{group_id}/members',
    response_model=list[uuid.UUID],
    dependencies=[Depends(require_tenant_permission(TenantPermission.GROUPS_MANAGE))],
)
async def set_group_members_endpoint(
    group_id: uuid.UUID, payload: GroupMembersUpdate, tenant: CurrentTenantDep, db: DbSessionDep
) -> list[uuid.UUID]:
    """PUT because the body is the whole roster, not an addition to it."""
    try:
        return await set_group_members(
            GroupRepository(db),
            PersonRepository(db),
            tenant_id=tenant.id,
            group_id=group_id,
            person_ids=payload.person_ids,
        )
    except GroupNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Group not found') from exc
    except PersonNotInTenantError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            'One or more people do not belong to this tenant',
        ) from exc


@router.put(
    '/{group_id}/supervisors',
    response_model=list[uuid.UUID],
    dependencies=[Depends(require_tenant_permission(TenantPermission.GROUPS_MANAGE))],
)
async def set_group_supervisors_endpoint(
    group_id: uuid.UUID,
    payload: GroupSupervisorsUpdate,
    tenant: CurrentTenantDep,
    db: DbSessionDep,
) -> list[uuid.UUID]:
    """Who may mark this group's attendance. Admin-only on purpose: a teacher
    must not be able to add themselves to another teacher's class."""
    try:
        return await set_group_supervisors(
            GroupRepository(db),
            TenantUserRepository(db),
            tenant_id=tenant.id,
            group_id=group_id,
            tenant_user_ids=payload.tenant_user_ids,
        )
    except GroupNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Group not found') from exc
    except SupervisorNotInTenantError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            'One or more users do not belong to this tenant',
        ) from exc
