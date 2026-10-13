import uuid
from datetime import date as date_type
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import (
    CurrentTenantDep,
    CurrentTenantUserDep,
    DbSessionDep,
    require_tenant_feature,
    require_tenant_permission,
)
from app.domains.attendance.repository import AttendanceRepository
from app.domains.attendance.schemas import (
    AttendanceDayUpsert,
    AttendanceRecordRead,
    AttendanceSummaryRead,
)
from app.domains.attendance.service import (
    InvalidDateRangeError,
    PersonNotInTenantError,
    PersonOutOfScopeError,
    list_absentees,
    list_attendance_for_date,
    mark_attendance,
    summarize_attendance,
)
from app.domains.group.repository import GroupRepository
from app.domains.group.service import list_supervised_person_ids
from app.domains.person.repository import PersonRepository
from app.domains.tenant_user.permissions import TenantPermission, role_has_permission

# The feature key a platform admin must have enabled for this tenant. Gated
# on every route below, not just hidden in the UI - see require_tenant_feature.
ATTENDANCE_FEATURE_KEY = 'attendance'

router = APIRouter(
    prefix='/tenant/attendance',
    tags=['tenant-attendance'],
    dependencies=[Depends(require_tenant_feature(ATTENDANCE_FEATURE_KEY))],
)


async def resolve_attendance_scope(
    user: CurrentTenantUserDep, db: DbSessionDep
) -> set[uuid.UUID] | None:
    """The people this user may see and mark, or None for no restriction.

    An office admin holds ATTENDANCE_MANAGE_ALL and gets the whole tenant.
    Everyone else - a homeroom teacher - gets exactly the members of the
    groups they supervise, which is an empty set if they supervise none.
    This is the security boundary; the group picker in the UI is only a
    convenience on top of it.
    """
    if role_has_permission(user.role, TenantPermission.ATTENDANCE_MANAGE_ALL):
        return None
    return await list_supervised_person_ids(
        GroupRepository(db), tenant_id=user.tenant_id, tenant_user_id=user.id
    )


AttendanceScopeDep = Annotated[set[uuid.UUID] | None, Depends(resolve_attendance_scope)]


@router.get(
    '',
    response_model=list[AttendanceRecordRead],
    dependencies=[Depends(require_tenant_permission(TenantPermission.ATTENDANCE_VIEW))],
)
async def list_attendance_endpoint(
    tenant: CurrentTenantDep,
    db: DbSessionDep,
    scope: AttendanceScopeDep,
    date: Annotated[date_type, Query()],
) -> list[AttendanceRecordRead]:
    records = await list_attendance_for_date(
        AttendanceRepository(db), tenant_id=tenant.id, date=date, scope=scope
    )
    return [AttendanceRecordRead.model_validate(record) for record in records]


@router.get(
    '/absentees',
    response_model=list[AttendanceRecordRead],
    dependencies=[Depends(require_tenant_permission(TenantPermission.ATTENDANCE_VIEW))],
)
async def list_absentees_endpoint(
    tenant: CurrentTenantDep,
    db: DbSessionDep,
    scope: AttendanceScopeDep,
    date: Annotated[date_type, Query()],
) -> list[AttendanceRecordRead]:
    """Who was absent on a date - the input to the daily guardian notices."""
    records = await list_absentees(
        AttendanceRepository(db), tenant_id=tenant.id, date=date, scope=scope
    )
    return [AttendanceRecordRead.model_validate(record) for record in records]


@router.get(
    '/summary',
    response_model=list[AttendanceSummaryRead],
    dependencies=[Depends(require_tenant_permission(TenantPermission.ATTENDANCE_VIEW))],
)
async def attendance_summary_endpoint(
    tenant: CurrentTenantDep,
    db: DbSessionDep,
    scope: AttendanceScopeDep,
    start: Annotated[date_type, Query()],
    end: Annotated[date_type, Query()],
) -> list[AttendanceSummaryRead]:
    try:
        return await summarize_attendance(
            AttendanceRepository(db), tenant_id=tenant.id, start=start, end=end, scope=scope
        )
    except InvalidDateRangeError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, 'End date must not be before start date'
        ) from exc


@router.put(
    '',
    response_model=list[AttendanceRecordRead],
    dependencies=[Depends(require_tenant_permission(TenantPermission.ATTENDANCE_MANAGE))],
)
async def mark_attendance_endpoint(
    payload: AttendanceDayUpsert,
    tenant: CurrentTenantDep,
    db: DbSessionDep,
    scope: AttendanceScopeDep,
) -> list[AttendanceRecordRead]:
    """PUT, not POST: marking a day is idempotent. Re-submitting corrects the
    existing records rather than creating a second set for the same date."""
    try:
        records = await mark_attendance(
            AttendanceRepository(db),
            PersonRepository(db),
            tenant_id=tenant.id,
            date=payload.date,
            records=payload.records,
            scope=scope,
        )
    except PersonNotInTenantError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            'One or more people do not belong to this tenant',
        ) from exc
    except PersonOutOfScopeError as exc:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            'One or more people are outside the groups you supervise',
        ) from exc
    return [AttendanceRecordRead.model_validate(record) for record in records]
