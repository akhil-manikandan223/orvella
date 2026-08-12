import uuid
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import ActorContext, current_actor_ctx_var
from app.core.config import Settings, get_settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.domains.platform_admin.models import PlatformAdmin
from app.domains.platform_admin.repository import PlatformAdminRepository
from app.domains.tenant.models import Tenant
from app.domains.tenant.repository import TenantRepository
from app.domains.tenant.service import resolve_tenant_by_host

SettingsDep = Annotated[Settings, Depends(get_settings)]
DbSessionDep = Annotated[AsyncSession, Depends(get_db)]

# auto_error=False so a missing Authorization header falls through to our own
# 401 below, instead of HTTPBearer's default (and inconsistent) 403.
_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_platform_admin(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    settings: SettingsDep,
    db: DbSessionDep,
) -> PlatformAdmin:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    if credentials is None:
        raise credentials_exception

    try:
        payload = decode_access_token(credentials.credentials, settings)
    except jwt.InvalidTokenError as exc:
        raise credentials_exception from exc

    if payload.get('type') != 'platform_admin':
        raise credentials_exception

    raw_admin_id = payload.get('sub')
    if raw_admin_id is None:
        raise credentials_exception

    try:
        admin_id = uuid.UUID(raw_admin_id)
    except ValueError as exc:
        raise credentials_exception from exc

    repository = PlatformAdminRepository(db)
    admin = await repository.get_by_id(admin_id)

    if admin is None or not admin.is_active:
        raise credentials_exception

    current_actor_ctx_var.set(ActorContext('platform_admin', admin.id))
    return admin


CurrentPlatformAdminDep = Annotated[PlatformAdmin, Depends(get_current_platform_admin)]


async def get_tenant_from_host(
    request: Request,
    db: DbSessionDep,
    settings: SettingsDep,
) -> Tenant | None:
    """Resolve a Tenant from the request's Host header, if any.

    Defined for Phase 3+ to Depends() on once tenant-scoped routes exist.
    Not wired into any router or middleware yet - there is nothing to
    enforce it against until tenant-scoped auth exists.
    """
    repository = TenantRepository(db)
    return await resolve_tenant_by_host(
        repository, request.headers.get('host'), base_domain=settings.base_domain
    )


OptionalTenantFromHostDep = Annotated[Tenant | None, Depends(get_tenant_from_host)]
