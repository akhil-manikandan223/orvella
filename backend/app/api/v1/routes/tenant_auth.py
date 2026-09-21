from fastapi import APIRouter, HTTPException, Request, Response, status

from app.api.deps import CurrentTenantDep, CurrentTenantUserDep, DbSessionDep, SettingsDep
from app.core.refresh_cookie import (
    TENANT_USER_COOKIE_NAME,
    TENANT_USER_COOKIE_PATH,
    clear_refresh_cookie,
    set_refresh_cookie,
)
from app.core.security import create_access_token
from app.domains.auth_session.repository import RefreshTokenRepository
from app.domains.auth_session.service import (
    RefreshTokenInvalidError,
    issue_refresh_token,
    revoke_refresh_token,
    rotate_refresh_token,
)
from app.domains.feature.repository import FeatureRepository
from app.domains.tenant.repository import TenantFeatureRepository
from app.domains.tenant_user.repository import TenantUserRepository
from app.domains.tenant_user.schemas import (
    HeroFeatureRead,
    TenantChangePasswordRequest,
    TenantContextRead,
    TenantLoginContextRead,
    TenantLoginRequest,
    TenantMeRead,
    TenantThemePreferenceUpdate,
    TenantTokenResponse,
    TenantUserRead,
)
from app.domains.tenant_user.service import (
    InvalidCredentialsError,
    authenticate_tenant_user,
    change_tenant_user_password,
)

router = APIRouter(prefix='/tenant/auth', tags=['tenant-auth'])


@router.post('/login', response_model=TenantTokenResponse)
async def tenant_login(
    payload: TenantLoginRequest,
    tenant: CurrentTenantDep,
    response: Response,
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

    refresh_token_repository = RefreshTokenRepository(db)
    _, raw_refresh_token = await issue_refresh_token(
        refresh_token_repository,
        subject_type='tenant_user',
        subject_id=user.id,
        tenant_id=tenant.id,
        ttl_days=settings.refresh_token_expire_days,
    )
    set_refresh_cookie(
        response,
        name=TENANT_USER_COOKIE_NAME,
        path=TENANT_USER_COOKIE_PATH,
        value=raw_refresh_token,
        max_age_days=settings.refresh_token_expire_days,
        settings=settings,
    )

    return TenantTokenResponse(access_token=access_token)


@router.post('/refresh', response_model=TenantTokenResponse)
async def tenant_refresh(
    request: Request,
    response: Response,
    tenant: CurrentTenantDep,
    db: DbSessionDep,
    settings: SettingsDep,
) -> TenantTokenResponse:
    raw_refresh_token = request.cookies.get(TENANT_USER_COOKIE_NAME)
    if raw_refresh_token is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, 'Not signed in')

    repository = RefreshTokenRepository(db)
    try:
        new_row, new_raw_refresh_token = await rotate_refresh_token(
            repository,
            raw_token=raw_refresh_token,
            subject_type='tenant_user',
            ttl_days=settings.refresh_token_expire_days,
        )
    except RefreshTokenInvalidError as exc:
        clear_refresh_cookie(response, name=TENANT_USER_COOKIE_NAME, path=TENANT_USER_COOKIE_PATH)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, 'Session expired') from exc

    # A refresh token minted on one tenant's subdomain must not mint access
    # tokens while on another's - same invariant as the access token's own
    # tenant_id claim check in get_current_tenant_user.
    if new_row.tenant_id != tenant.id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, 'Session expired')

    user_repository = TenantUserRepository(db)
    user = await user_repository.get_by_id(new_row.subject_id)
    if user is None or not user.is_active or user.tenant_id != tenant.id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, 'Session expired')

    access_token = create_access_token(
        subject=str(user.id),
        token_type='tenant_user',
        settings=settings,
        extra_claims={'tenant_id': str(tenant.id)},
    )
    set_refresh_cookie(
        response,
        name=TENANT_USER_COOKIE_NAME,
        path=TENANT_USER_COOKIE_PATH,
        value=new_raw_refresh_token,
        max_age_days=settings.refresh_token_expire_days,
        settings=settings,
    )
    return TenantTokenResponse(access_token=access_token)


@router.post('/logout', status_code=status.HTTP_204_NO_CONTENT)
async def tenant_logout(request: Request, response: Response, db: DbSessionDep) -> None:
    # Deliberately not gated behind CurrentTenantUserDep - see the matching
    # note on the platform-admin /auth/logout.
    raw_refresh_token = request.cookies.get(TENANT_USER_COOKIE_NAME)
    if raw_refresh_token is not None:
        repository = RefreshTokenRepository(db)
        await revoke_refresh_token(repository, raw_token=raw_refresh_token)
    clear_refresh_cookie(response, name=TENANT_USER_COOKIE_NAME, path=TENANT_USER_COOKIE_PATH)


@router.get('/me', response_model=TenantMeRead)
async def read_current_tenant_user(
    user: CurrentTenantUserDep, tenant: CurrentTenantDep
) -> TenantMeRead:
    return TenantMeRead(
        user=TenantUserRead.model_validate(user),
        tenant=TenantContextRead(id=tenant.id, name=tenant.name, slug=tenant.slug),
    )


@router.put('/theme', response_model=TenantUserRead)
async def set_tenant_theme_preference(
    payload: TenantThemePreferenceUpdate, user: CurrentTenantUserDep, db: DbSessionDep
) -> TenantUserRead:
    repository = TenantUserRepository(db)
    updated = await repository.update(user, theme_preference=payload.theme_preference)
    return TenantUserRead.model_validate(updated)


@router.post('/change-password', status_code=status.HTTP_204_NO_CONTENT)
async def change_tenant_password(
    payload: TenantChangePasswordRequest, user: CurrentTenantUserDep, db: DbSessionDep
) -> None:
    repository = TenantUserRepository(db)
    try:
        await change_tenant_user_password(
            repository,
            user,
            current_password=payload.current_password,
            new_password=payload.new_password,
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Current password is incorrect',
        ) from exc


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
