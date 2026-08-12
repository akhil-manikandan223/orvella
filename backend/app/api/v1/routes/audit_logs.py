import uuid

from fastapi import APIRouter, Depends

from app.api.deps import DbSessionDep, get_current_platform_admin
from app.domains.audit_log.repository import AuditLogRepository
from app.domains.audit_log.schemas import AuditLogRead
from app.domains.audit_log.service import list_audit_logs

router = APIRouter(
    prefix='/platform-admin/audit-logs',
    tags=['audit-logs'],
    dependencies=[Depends(get_current_platform_admin)],
)


@router.get('', response_model=list[AuditLogRead])
async def list_audit_logs_endpoint(
    db: DbSessionDep,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    tenant_id: uuid.UUID | None = None,
) -> list[AuditLogRead]:
    repository = AuditLogRepository(db)
    logs = await list_audit_logs(
        repository, entity_type=entity_type, entity_id=entity_id, tenant_id=tenant_id
    )
    return [AuditLogRead.model_validate(log) for log in logs]
