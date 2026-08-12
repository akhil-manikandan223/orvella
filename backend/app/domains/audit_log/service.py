import uuid

from app.domains.audit_log.models import AuditLog
from app.domains.audit_log.repository import AuditLogRepository


async def list_audit_logs(
    repository: AuditLogRepository,
    *,
    entity_type: str | None,
    entity_id: uuid.UUID | None,
    tenant_id: uuid.UUID | None,
) -> list[AuditLog]:
    return await repository.list_filtered(
        entity_type=entity_type, entity_id=entity_id, tenant_id=tenant_id
    )
