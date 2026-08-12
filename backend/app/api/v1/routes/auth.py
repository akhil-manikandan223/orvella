from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentPlatformAdminDep, DbSessionDep, SettingsDep
from app.core.security import create_access_token
from app.domains.platform_admin.repository import PlatformAdminRepository
from app.domains.platform_admin.schemas import LoginRequest, PlatformAdminRead, TokenResponse
from app.domains.platform_admin.service import InvalidCredentialsError, authenticate_platform_admin

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
