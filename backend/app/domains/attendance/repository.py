import uuid
from datetime import date as date_type

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.attendance.models import AttendanceRecord


class AttendanceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_date(
        self,
        *,
        tenant_id: uuid.UUID,
        date: date_type,
        person_ids: set[uuid.UUID] | None = None,
    ) -> list[AttendanceRecord]:
        """`person_ids` of None means every person in the tenant; an empty set
        means nobody, which is what a supervisor of no groups should see."""
        query = select(AttendanceRecord).where(
            AttendanceRecord.tenant_id == tenant_id, AttendanceRecord.date == date
        )
        if person_ids is not None:
            query = query.where(AttendanceRecord.person_id.in_(person_ids))
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def list_for_range(
        self,
        *,
        tenant_id: uuid.UUID,
        start: date_type,
        end: date_type,
        person_id: uuid.UUID | None = None,
    ) -> list[AttendanceRecord]:
        query = select(AttendanceRecord).where(
            AttendanceRecord.tenant_id == tenant_id,
            AttendanceRecord.date >= start,
            AttendanceRecord.date <= end,
        )
        if person_id is not None:
            query = query.where(AttendanceRecord.person_id == person_id)
        result = await self._session.execute(query.order_by(AttendanceRecord.date))
        return list(result.scalars().all())

    async def summarize_range(
        self,
        *,
        tenant_id: uuid.UUID,
        start: date_type,
        end: date_type,
        person_ids: set[uuid.UUID] | None = None,
    ) -> list[tuple[uuid.UUID, str, int]]:
        """(person_id, status, count) aggregated in the database.

        Counted in SQL rather than by loading every row: a month of a
        1500-person college is ~30k rows, and the report only needs the
        totals.
        """
        query = select(
            AttendanceRecord.person_id,
            AttendanceRecord.status,
            func.count().label('count'),
        ).where(
            AttendanceRecord.tenant_id == tenant_id,
            AttendanceRecord.date >= start,
            AttendanceRecord.date <= end,
        )
        if person_ids is not None:
            query = query.where(AttendanceRecord.person_id.in_(person_ids))
        result = await self._session.execute(
            query.group_by(AttendanceRecord.person_id, AttendanceRecord.status)
        )
        return [(row.person_id, row.status, row.count) for row in result.all()]

    async def upsert_many(
        self,
        *,
        tenant_id: uuid.UUID,
        date: date_type,
        entries: list[tuple[uuid.UUID, str, str | None]],
    ) -> list[AttendanceRecord]:
        """Marks a day for several people, updating any already marked.

        Re-marking a day is normal (a correction, a late arrival resolved),
        so this updates in place rather than inserting a duplicate that the
        unique constraint would reject anyway.
        """
        existing = {
            record.person_id: record
            for record in await self.list_for_date(tenant_id=tenant_id, date=date)
        }

        saved: list[AttendanceRecord] = []
        for person_id, status, note in entries:
            record = existing.get(person_id)
            if record is None:
                record = AttendanceRecord(
                    tenant_id=tenant_id,
                    person_id=person_id,
                    date=date,
                    status=status,
                    note=note,
                )
                self._session.add(record)
            else:
                record.status = status
                record.note = note
            saved.append(record)

        await self._session.commit()
        for record in saved:
            await self._session.refresh(record)
        return saved
