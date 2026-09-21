from fastapi import APIRouter, HTTPException, Request, Response, status

from app.api.deps import CurrentPlatformAdminDep, DbSessionDep, SettingsDep
from app.core.refresh_cookie import (
    PLATFORM_ADMIN_COOKIE_NAME,
    PLATFORM_ADMIN_COOKIE_PATH,
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
from app.domains.platform_admin.repository import PlatformAdminRepository
from app.domains.platform_admin.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    PlatformAdminRead,
    ThemePreferenceUpdate,
    TokenResponse,
)
from app.domains.platform_admin.service import (
    InvalidCredentialsError,
    authenticate_platform_admin,
    change_platform_admin_password,
)

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post('/login', response_model=TokenResponse)
async def login(
    payload: LoginRequest, response: Response, db: DbSessionDep, settings: SettingsDep
) -> TokenResponse:
    repository = PlatformAdminRepository(db)
    try:
        admin = await authenticate_platform_admin(
            repository, email=payload.email, password=payload.password
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect email or password',
        ) from exc

    access_token = create_access_token(
        subject=str(admin.id), token_type='platform_admin', settings=settings
    )

    refresh_token_repository = RefreshTokenRepository(db)
    _, raw_refresh_token = await issue_refresh_token(
        refresh_token_repository,
        subject_type='platform_admin',
        subject_id=admin.id,
        tenant_id=None,
        ttl_days=settings.refresh_token_expire_days,
    )
    set_refresh_cookie(
        response,
        name=PLATFORM_ADMIN_COOKIE_NAME,
        path=PLATFORM_ADMIN_COOKIE_PATH,
        value=raw_refresh_token,
        max_age_days=settings.refresh_token_expire_days,
        settings=settings,
    )

    return TokenResponse(access_token=access_token)


@router.post('/refresh', response_model=TokenResponse)
async def refresh(
    request: Request, response: Response, db: DbSessionDep, settings: SettingsDep
) -> TokenResponse:
    raw_refresh_token = request.cookies.get(PLATFORM_ADMIN_COOKIE_NAME)
    if raw_refresh_token is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, 'Not signed in')

    repository = RefreshTokenRepository(db)
    try:
        new_row, new_raw_refresh_token = await rotate_refresh_token(
            repository,
            raw_token=raw_refresh_token,
            subject_type='platform_admin',
            ttl_days=settings.refresh_token_expire_days,
        )
    except RefreshTokenInvalidError as exc:
        clear_refresh_cookie(
            response, name=PLATFORM_ADMIN_COOKIE_NAME, path=PLATFORM_ADMIN_COOKIE_PATH
        )
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, 'Session expired') from exc

    admin_repository = PlatformAdminRepository(db)
    admin = await admin_repository.get_by_id(new_row.subject_id)
    if admin is None or not admin.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, 'Session expired')

    access_token = create_access_token(
        subject=str(admin.id), token_type='platform_admin', settings=settings
    )
    set_refresh_cookie(
        response,
        name=PLATFORM_ADMIN_COOKIE_NAME,
        path=PLATFORM_ADMIN_COOKIE_PATH,
        value=new_raw_refresh_token,
        max_age_days=settings.refresh_token_expire_days,
        settings=settings,
    )
    return TokenResponse(access_token=access_token)


@router.post('/logout', status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response, db: DbSessionDep) -> None:
    # Deliberately not gated behind CurrentPlatformAdminDep: a user with an
    # already-expired access token must still be able to log out (that's
    # exactly when the refresh cookie is the only thing left to revoke).
    raw_refresh_token = request.cookies.get(PLATFORM_ADMIN_COOKIE_NAME)
    if raw_refresh_token is not None:
        repository = RefreshTokenRepository(db)
        await revoke_refresh_token(repository, raw_token=raw_refresh_token)
    clear_refresh_cookie(response, name=PLATFORM_ADMIN_COOKIE_NAME, path=PLATFORM_ADMIN_COOKIE_PATH)


@router.get('/me', response_model=PlatformAdminRead)
async def read_current_admin(admin: CurrentPlatformAdminDep) -> PlatformAdminRead:
    return PlatformAdminRead.model_validate(admin)


@router.put('/theme', response_model=PlatformAdminRead)
async def set_theme_preference(
    payload: ThemePreferenceUpdate, admin: CurrentPlatformAdminDep, db: DbSessionDep
) -> PlatformAdminRead:
    repository = PlatformAdminRepository(db)
    updated = await repository.update(admin, theme_preference=payload.theme_preference)
    return PlatformAdminRead.model_validate(updated)


@router.post('/change-password', status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    payload: ChangePasswordRequest, admin: CurrentPlatformAdminDep, db: DbSessionDep
) -> None:
    repository = PlatformAdminRepository(db)
    try:
        await change_platform_admin_password(
            repository,
            admin,
            current_password=payload.current_password,
            new_password=payload.new_password,
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Current password is incorrect',
        ) from exc
