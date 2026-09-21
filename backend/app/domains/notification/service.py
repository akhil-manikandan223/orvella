import uuid

from app.domains.notification.models import Notification
from app.domains.notification.repository import NotificationRepository
from app.domains.notification.schemas import NotificationRead
from app.domains.notification.ws_manager import notification_connections


class NotificationNotFoundError(Exception):
    pass


async def create_notification(
    repository: NotificationRepository,
    *,
    tenant_id: uuid.UUID,
    tenant_user_id: uuid.UUID,
    type: str,
    title: str,
    message: str,
) -> Notification:
    notification = await repository.create(
        tenant_id=tenant_id,
        tenant_user_id=tenant_user_id,
        type=type,
        title=title,
        message=message,
    )
    notification_data = NotificationRead.model_validate(notification).model_dump(mode='json')
    await notification_connections.send_to_user(
        tenant_user_id, {'event': 'notification', 'data': notification_data}
    )
    return notification


async def list_notifications(
    repository: NotificationRepository, *, tenant_id: uuid.UUID, tenant_user_id: uuid.UUID
) -> list[Notification]:
    return await repository.list_for_user(tenant_id=tenant_id, tenant_user_id=tenant_user_id)


async def get_unread_count(
    repository: NotificationRepository, *, tenant_id: uuid.UUID, tenant_user_id: uuid.UUID
) -> int:
    return await repository.count_unread(tenant_id=tenant_id, tenant_user_id=tenant_user_id)


async def mark_notification_read(
    repository: NotificationRepository,
    *,
    tenant_id: uuid.UUID,
    tenant_user_id: uuid.UUID,
    notification_id: uuid.UUID,
) -> Notification:
    notification = await repository.get_by_id(notification_id)
    if (
        notification is None
        or notification.tenant_id != tenant_id
        or notification.tenant_user_id != tenant_user_id
    ):
        raise NotificationNotFoundError
    if notification.read_at is not None:
        return notification
    return await repository.mark_read(notification)


async def mark_all_notifications_read(
    repository: NotificationRepository, *, tenant_id: uuid.UUID, tenant_user_id: uuid.UUID
) -> None:
    await repository.mark_all_read(tenant_id=tenant_id, tenant_user_id=tenant_user_id)
