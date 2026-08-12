import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.audit_log.models import AuditLog


class AuditLogRepository:
    """Read-only: AuditLog rows are written solely by app.core.audit's listener."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_filtered(
        self,
        *,
        entity_type: str | None = None,
        entity_id: uuid.UUID | None = None,
        tenant_id: uuid.UUID | None = None,
    ) -> list[AuditLog]:
        query = select(AuditLog).order_by(AuditLog.created_at.desc())
        if entity_type is not None:
            query = query.where(AuditLog.entity_type == entity_type)
        if entity_id is not None:
            query = query.where(AuditLog.entity_id == entity_id)
        if tenant_id is not None:
            query = query.where(AuditLog.tenant_id == tenant_id)
        result = await self._session.execute(query)
        return list(result.scalars().all())
