import uuid
from collections import defaultdict
from datetime import date as date_type

from app.domains.attendance.models import AttendanceRecord
from app.domains.attendance.repository import AttendanceRepository
from app.domains.attendance.schemas import AttendanceRecordUpsert, AttendanceSummaryRead
from app.domains.person.repository import PersonRepository


class PersonNotInTenantError(Exception):
    pass


class InvalidDateRangeError(Exception):
    pass


async def _assert_people_in_tenant(
    person_repository: PersonRepository,
    *,
    tenant_id: uuid.UUID,
    person_ids: set[uuid.UUID],
) -> None:
    """Every person marked must belong to the calling tenant.

    The tenant comes from the subdomain, but the person_ids come from the
    request body - so without this check a tenant admin could write
    attendance against another tenant's people. One query for the whole
    roster rather than one per person.
    """
    owned = {person.id for person in await person_repository.list_for_tenant(tenant_id)}
    if not person_ids <= owned:
        raise PersonNotInTenantError


class PersonOutOfScopeError(Exception):
    pass


def _assert_within_scope(
    person_ids: set[uuid.UUID], scope: set[uuid.UUID] | None
) -> None:
    """`scope` of None means unrestricted (a tenant admin).

    For anyone else it's the set of people they supervise, and marking
    outside it is refused - the department dropdown in the UI is a filter,
    not a boundary, so the boundary has to live here.
    """
    if scope is not None and not person_ids <= scope:
        raise PersonOutOfScopeError


async def mark_attendance(
    repository: AttendanceRepository,
    person_repository: PersonRepository,
    *,
    tenant_id: uuid.UUID,
    date: date_type,
    records: list[AttendanceRecordUpsert],
    scope: set[uuid.UUID] | None = None,
) -> list[AttendanceRecord]:
    if not records:
        return []

    person_ids = {record.person_id for record in records}
    await _assert_people_in_tenant(
        person_repository, tenant_id=tenant_id, person_ids=person_ids
    )
    _assert_within_scope(person_ids, scope)
    return await repository.upsert_many(
        tenant_id=tenant_id,
        date=date,
        entries=[(r.person_id, r.status, r.note) for r in records],
    )


async def list_attendance_for_date(
    repository: AttendanceRepository,
    *,
    tenant_id: uuid.UUID,
    date: date_type,
    scope: set[uuid.UUID] | None = None,
) -> list[AttendanceRecord]:
    return await repository.list_for_date(tenant_id=tenant_id, date=date, person_ids=scope)


async def list_absentees(
    repository: AttendanceRepository,
    *,
    tenant_id: uuid.UUID,
    date: date_type,
    scope: set[uuid.UUID] | None = None,
) -> list[AttendanceRecord]:
    """Who to notify for a given day. 'Late' deliberately doesn't count -
    they turned up."""
    records = await repository.list_for_date(tenant_id=tenant_id, date=date, person_ids=scope)
    return [record for record in records if record.status == 'absent']


async def summarize_attendance(
    repository: AttendanceRepository,
    *,
    tenant_id: uuid.UUID,
    start: date_type,
    end: date_type,
    scope: set[uuid.UUID] | None = None,
) -> list[AttendanceSummaryRead]:
    if end < start:
        raise InvalidDateRangeError

    counts: dict[uuid.UUID, dict[str, int]] = defaultdict(
        lambda: {'present': 0, 'absent': 0, 'late': 0, 'excused': 0}
    )
    for person_id, status, count in await repository.summarize_range(
        tenant_id=tenant_id, start=start, end=end, person_ids=scope
    ):
        counts[person_id][status] = count

    return [
        AttendanceSummaryRead(
            person_id=person_id,
            present=tallies['present'],
            absent=tallies['absent'],
            late=tallies['late'],
            excused=tallies['excused'],
            total=sum(tallies.values()),
        )
        for person_id, tallies in counts.items()
    ]
