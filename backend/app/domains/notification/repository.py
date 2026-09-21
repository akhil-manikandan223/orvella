import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.notification.models import Notification

_LIST_LIMIT = 50


class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, notification_id: uuid.UUID) -> Notification | None:
        result = await self._session.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self, *, tenant_id: uuid.UUID, tenant_user_id: uuid.UUID
    ) -> list[Notification]:
        result = await self._session.execute(
            select(Notification)
            .where(
                Notification.tenant_id == tenant_id,
                Notification.tenant_user_id == tenant_user_id,
            )
            .order_by(Notification.created_at.desc())
            .limit(_LIST_LIMIT)
        )
        return list(result.scalars().all())

    async def count_unread(self, *, tenant_id: uuid.UUID, tenant_user_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.tenant_id == tenant_id,
                Notification.tenant_user_id == tenant_user_id,
                Notification.read_at.is_(None),
            )
        )
        return result.scalar_one()

    async def create(
        self,
        *,
        tenant_id: uuid.UUID,
        tenant_user_id: uuid.UUID,
        type: str,
        title: str,
        message: str,
    ) -> Notification:
        notification = Notification(
            tenant_id=tenant_id,
            tenant_user_id=tenant_user_id,
            type=type,
            title=title,
            message=message,
        )
        self._session.add(notification)
        await self._session.commit()
        await self._session.refresh(notification)
        return notification

    async def mark_read(self, notification: Notification) -> Notification:
        notification.read_at = datetime.now(UTC)
        await self._session.commit()
        await self._session.refresh(notification)
        return notification

    async def mark_all_read(self, *, tenant_id: uuid.UUID, tenant_user_id: uuid.UUID) -> None:
        await self._session.execute(
            update(Notification)
            .where(
                Notification.tenant_id == tenant_id,
                Notification.tenant_user_id == tenant_user_id,
                Notification.read_at.is_(None),
            )
            .values(read_at=datetime.now(UTC))
        )
        await self._session.commit()
