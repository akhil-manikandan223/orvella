import uuid
from datetime import date as date_type
from typing import Literal

from pydantic import BaseModel, ConfigDict

AttendanceStatus = Literal['present', 'absent', 'late', 'excused']


class AttendanceRecordUpsert(BaseModel):
    person_id: uuid.UUID
    status: AttendanceStatus
    note: str | None = None


class AttendanceDayUpsert(BaseModel):
    """A whole day marked in one call.

    Attendance is taken for a group at once, not person by person, so the
    write side mirrors that: one request per day, with the roster in it.
    Saves a round trip per student and keeps the day's marking atomic.
    """

    date: date_type
    records: list[AttendanceRecordUpsert]


class AttendanceRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    person_id: uuid.UUID
    date: date_type
    status: AttendanceStatus
    note: str | None


class AttendanceSummaryRead(BaseModel):
    """Per-person totals over a date range - what the monthly report needs."""

    person_id: uuid.UUID
    present: int
    absent: int
    late: int
    excused: int
    total: int
