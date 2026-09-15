from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentTenantDep, CurrentTenantUserDep, DbSessionDep, SettingsDep
from app.core.security import create_access_token
from app.domains.feature.repository import FeatureRepository
from app.domains.tenant.repository import TenantFeatureRepository
from app.domains.tenant_user.repository import TenantUserRepository
from app.domains.tenant_user.schemas import (
    HeroFeatureRead,
    TenantContextRead,
    TenantLoginContextRead,
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


@router.get('/context', response_model=TenantLoginContextRead)
async def read_tenant_login_context(
    tenant: CurrentTenantDep, db: DbSessionDep
) -> TenantLoginContextRead:
    """Public (no auth) info for the tenant login page's hero tiles.

    No auth on purpose - this page is reached before any login. Which
    features it exposes is controlled server-side by the tenant's own
    login_hero_mode setting, not by anything the client sends.
    """
    feature_repository = FeatureRepository(db)

    if tenant.login_hero_mode == 'featured':
        tenant_feature_repository = TenantFeatureRepository(db)
        tenant_features = await tenant_feature_repository.list_for_tenant(tenant.id)
        enabled_feature_ids = [tf.feature_id for tf in tenant_features if tf.enabled]
        features = await feature_repository.list_by_ids(enabled_feature_ids)
    else:
        features = [f for f in await feature_repository.list_all() if f.status == 'active']

    return TenantLoginContextRead(
        tenant=TenantContextRead(id=tenant.id, name=tenant.name, slug=tenant.slug),
        hero_features=sorted(
            (
                HeroFeatureRead(key=f.key, name=f.name, description=f.description)
                for f in features
            ),
            key=lambda f: f.name,
        ),
    )
