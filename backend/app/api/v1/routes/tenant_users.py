from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import CurrentTenantDep, DbSessionDep, require_tenant_permission
from app.domains.tenant_user.permissions import TenantPermission
from app.domains.tenant_user.repository import TenantUserRepository
from app.domains.tenant_user.schemas import TenantUserCreate, TenantUserRead
from app.domains.tenant_user.service import (
    TenantUserAlreadyExistsError,
    create_tenant_user,
    list_tenant_users,
)

router = APIRouter(prefix='/tenant/users', tags=['tenant-users'])


@router.get(
    '',
    response_model=list[TenantUserRead],
    dependencies=[Depends(require_tenant_permission(TenantPermission.TENANT_USERS_VIEW))],
)
async def list_my_tenant_users(tenant: CurrentTenantDep, db: DbSessionDep) -> list[TenantUserRead]:
    repository = TenantUserRepository(db)
    users = await list_tenant_users(repository, tenant_id=tenant.id)
    return [TenantUserRead.model_validate(user) for user in users]


@router.post(
    '',
    response_model=TenantUserRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_tenant_permission(TenantPermission.TENANT_USERS_MANAGE))],
)
async def create_my_tenant_user(
    payload: TenantUserCreate, tenant: CurrentTenantDep, db: DbSessionDep
) -> TenantUserRead:
    repository = TenantUserRepository(db)
    try:
        user = await create_tenant_user(
            repository,
            tenant_id=tenant.id,
            email=payload.email,
            password=payload.password,
            role=payload.role,
        )
    except TenantUserAlreadyExistsError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, 'A user with this email already exists for this tenant'
        ) from exc
    return TenantUserRead.model_validate(user)
