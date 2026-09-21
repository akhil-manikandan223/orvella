import uuid

import jwt
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status

from app.api.deps import CurrentTenantDep, CurrentTenantUserDep, DbSessionDep
from app.core.config import get_settings
from app.core.security import decode_access_token
from app.db.session import AsyncSessionLocal
from app.domains.notification.repository import NotificationRepository
from app.domains.notification.schemas import NotificationRead, UnreadCountRead
from app.domains.notification.service import (
    NotificationNotFoundError,
    get_unread_count,
    list_notifications,
    mark_all_notifications_read,
    mark_notification_read,
)
from app.domains.notification.ws_manager import notification_connections
from app.domains.tenant.repository import TenantRepository
from app.domains.tenant.service import resolve_tenant_by_host
from app.domains.tenant_user.repository import TenantUserRepository

router = APIRouter(prefix='/tenant/notifications', tags=['tenant-notifications'])


@router.get('', response_model=list[NotificationRead])
async def list_my_notifications(
    tenant: CurrentTenantDep, user: CurrentTenantUserDep, db: DbSessionDep
) -> list[NotificationRead]:
    repository = NotificationRepository(db)
    notifications = await list_notifications(
        repository, tenant_id=tenant.id, tenant_user_id=user.id
    )
    return [NotificationRead.model_validate(n) for n in notifications]


@router.get('/unread-count', response_model=UnreadCountRead)
async def get_my_unread_count(
    tenant: CurrentTenantDep, user: CurrentTenantUserDep, db: DbSessionDep
) -> UnreadCountRead:
    repository = NotificationRepository(db)
    count = await get_unread_count(repository, tenant_id=tenant.id, tenant_user_id=user.id)
    return UnreadCountRead(unread_count=count)


@router.post('/{notification_id}/read', response_model=NotificationRead)
async def mark_notification_read_endpoint(
    notification_id: uuid.UUID,
    tenant: CurrentTenantDep,
    user: CurrentTenantUserDep,
    db: DbSessionDep,
) -> NotificationRead:
    repository = NotificationRepository(db)
    try:
        notification = await mark_notification_read(
            repository,
            tenant_id=tenant.id,
            tenant_user_id=user.id,
            notification_id=notification_id,
        )
    except NotificationNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Notification not found') from exc
    return NotificationRead.model_validate(notification)


@router.post('/read-all', status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_notifications_read_endpoint(
    tenant: CurrentTenantDep, user: CurrentTenantUserDep, db: DbSessionDep
) -> None:
    repository = NotificationRepository(db)
    await mark_all_notifications_read(repository, tenant_id=tenant.id, tenant_user_id=user.id)


@router.websocket('/ws')
async def notifications_ws(websocket: WebSocket) -> None:
    """Pushes newly created notifications to the browser in real time.

    Not built on the CurrentTenant*/Depends() chain used by the HTTP routes
    above: those dependencies take a `Request`, which a WebSocket handshake
    never provides, so auth is re-derived manually here using the same
    checks `get_current_tenant_user` performs - token type/claims, the
    token's tenant_id matching the tenant resolved from this connection's
    Host header, and the user still being active. The browser's WebSocket
    API can't set an Authorization header, so the access token travels as a
    query param instead.
    """
    settings = get_settings()
    token = websocket.query_params.get('token')
    if token is None:
        await websocket.close(code=4401)
        return

    try:
        payload = decode_access_token(token, settings)
    except jwt.InvalidTokenError:
        await websocket.close(code=4401)
        return

    if payload.get('type') != 'tenant_user':
        await websocket.close(code=4401)
        return

    raw_user_id = payload.get('sub')
    raw_token_tenant_id = payload.get('tenant_id')
    if raw_user_id is None or raw_token_tenant_id is None:
        await websocket.close(code=4401)
        return

    try:
        user_id = uuid.UUID(raw_user_id)
        token_tenant_id = uuid.UUID(raw_token_tenant_id)
    except ValueError:
        await websocket.close(code=4401)
        return

    async with AsyncSessionLocal() as session:
        tenant = await resolve_tenant_by_host(
            TenantRepository(session),
            websocket.headers.get('host'),
            base_domain=settings.base_domain,
        )
        if tenant is None or tenant.id != token_tenant_id:
            await websocket.close(code=4401)
            return

        user = await TenantUserRepository(session).get_by_id(user_id)
        if user is None or not user.is_active or user.tenant_id != tenant.id:
            await websocket.close(code=4401)
            return

    await websocket.accept()
    notification_connections.connect(user.id, websocket)
    try:
        while True:
            # No messages are expected from the client - this just blocks
            # until the connection closes.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        notification_connections.disconnect(user.id, websocket)
