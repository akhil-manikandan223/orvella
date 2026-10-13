import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

ATTENDANCE_STATUSES = ('present', 'absent', 'late', 'excused')


class AttendanceRecord(Base):
    """One person's attendance for one day.

    Daily granularity on purpose: it serves the absentee notices and monthly
    reports this module exists for, and stays organisation-type-agnostic - a
    college, a gym and an office all mark a person present or not on a date.
    Per-session attendance (subject-wise, shift-wise) would need Scheduling
    to define what a session is, so it is deliberately out of scope here.
    """

    __tablename__ = 'attendance_records'
    __table_args__ = (
        # One record per person per day is the whole premise of daily
        # granularity - marking someone twice has to be an update, not a
        # second row, or every count downstream is wrong.
        UniqueConstraint('person_id', 'date', name='uq_attendance_records_person_date'),
        CheckConstraint(
            "status IN ('present', 'absent', 'late', 'excused')",
            name='ck_attendance_records_status',
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey('tenants.id'), index=True, nullable=False
    )
    person_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey('people.id', ondelete='CASCADE'),
        index=True,
        nullable=False,
    )
    date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
