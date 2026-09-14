from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentTenantDep, CurrentTenantUserDep, DbSessionDep, SettingsDep
from app.core.security import create_access_token
from app.domains.tenant_user.repository import TenantUserRepository
from app.domains.tenant_user.schemas import (
    TenantContextRead,
    TenantLoginRequest,
    TenantMeRead,
    TenantTokenResponse,
    TenantUserRead,
)
from app.domains.tenant_user.service import InvalidCredentialsError, authenticate_tenant_user

router = APIRouter(prefix='/tenant/auth', tags=['tenant-auth'])


@router.post('/login', response_model=TenantTokenResponse)
async def tenant_login(
    payload: TenantLoginRequest,
    tenant: CurrentTenantDep,
    db: DbSessionDep,
    settings: SettingsDep,
) -> TenantTokenResponse:
    repository = TenantUserRepository(db)
    try:
        user = await authenticate_tenant_user(
            repository, tenant_id=tenant.id, email=payload.email, password=payload.password
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect email or password',
        ) from exc

    access_token = create_access_token(
        subject=str(user.id),
        token_type='tenant_user',
        settings=settings,
        extra_claims={'tenant_id': str(tenant.id)},
    )
    return TenantTokenResponse(access_token=access_token)


@router.get('/me', response_model=TenantMeRead)
async def read_current_tenant_user(
    user: CurrentTenantUserDep, tenant: CurrentTenantDep
) -> TenantMeRead:
    return TenantMeRead(
        user=TenantUserRead.model_validate(user),
        tenant=TenantContextRead(id=tenant.id, name=tenant.name, slug=tenant.slug),
    )
