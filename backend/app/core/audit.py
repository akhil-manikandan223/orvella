import uuid
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from sqlalchemy import event, inspect
from sqlalchemy.orm import Session

from app.domains.audit_log.models import AuditLog
from app.domains.tenant.models import Tenant


@dataclass(frozen=True)
class ActorContext:
    actor_type: str
    actor_id: uuid.UUID


current_actor_ctx_var: ContextVar['ActorContext | None'] = ContextVar('current_actor', default=None)

# Mandatory: without excluding AuditLog from itself, writing an audit row
# triggers another flush, which this listener sees and audits again -
# crashes after ~100 nested flushes (SQLAlchemy's own re-flush guard limit),
# not just an infinite loop.
_EXCLUDED_MODELS: set[type] = {AuditLog}

# Only ORM unit-of-work mutations (session.add()/setattr()/session.delete())
# are captured here, via session.new/dirty/deleted below. Bulk Core-style
# `update(Model)...`/`delete(Model)...` statements bypass the unit-of-work
# entirely and are NOT audited - don't introduce those for tracked models
# without adding equivalent audit coverage elsewhere.


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, datetime | date):
        return value.isoformat()
    return value


def _resolve_tenant_id(obj: Any) -> uuid.UUID | None:
    if isinstance(obj, Tenant):
        return obj.id
    return getattr(obj, 'tenant_id', None)


def _row_dict(obj: Any) -> dict[str, Any]:
    return {c.key: _to_jsonable(getattr(obj, c.key)) for c in inspect(obj).mapper.column_attrs}


def _build_audit_log(obj: Any, *, action: str, changes: dict) -> AuditLog:
    actor = current_actor_ctx_var.get()
    return AuditLog(
        actor_type=actor.actor_type if actor else None,
        actor_id=actor.actor_id if actor else None,
        action=action,
        entity_type=type(obj).__tablename__,
        entity_id=obj.id,
        tenant_id=_resolve_tenant_id(obj),
        changes=changes,
    )


@event.listens_for(Session, 'after_flush')
def _record_audit_events(session: Session, flush_context: object) -> None:
    for obj in session.new:
        if type(obj) in _EXCLUDED_MODELS:
            continue
        session.add(_build_audit_log(obj, action='create', changes=_row_dict(obj)))

    for obj in session.dirty:
        if type(obj) in _EXCLUDED_MODELS:
            continue
        if not session.is_modified(obj, include_collections=False):
            continue
        insp = inspect(obj)
        changes: dict[str, Any] = {}
        for attr in insp.mapper.column_attrs:
            history = insp.attrs[attr.key].history
            if history.has_changes():
                changes[attr.key] = {
                    'old': _to_jsonable(history.deleted[0]) if history.deleted else None,
                    'new': _to_jsonable(history.added[0]) if history.added else None,
                }
        if changes:
            session.add(_build_audit_log(obj, action='update', changes=changes))

    for obj in session.deleted:
        if type(obj) in _EXCLUDED_MODELS:
            continue
        session.add(_build_audit_log(obj, action='delete', changes=_row_dict(obj)))
