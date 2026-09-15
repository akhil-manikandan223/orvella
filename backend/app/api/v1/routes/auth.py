from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentPlatformAdminDep, DbSessionDep, SettingsDep
from app.core.security import create_access_token
from app.domains.platform_admin.repository import PlatformAdminRepository
from app.domains.platform_admin.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    PlatformAdminRead,
    TokenResponse,
)
from app.domains.platform_admin.service import (
    InvalidCredentialsError,
    authenticate_platform_admin,
    change_platform_admin_password,
)

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post('/login', response_model=TokenResponse)
async def login(payload: LoginRequest, db: DbSessionDep, settings: SettingsDep) -> TokenResponse:
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
    return TokenResponse(access_token=access_token)


@router.get('/me', response_model=PlatformAdminRead)
async def read_current_admin(admin: CurrentPlatformAdminDep) -> PlatformAdminRead:
    return PlatformAdminRead.model_validate(admin)


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
        # Not 401: that status is reserved app-wide (see authInterceptor) for
        # "your token is invalid, log out" - this is an authenticated user
        # simply getting a form field wrong, which must not force a logout.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Current password is incorrect',
        ) from exc
