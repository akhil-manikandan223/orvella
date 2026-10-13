export type AttendanceStatus = 'present' | 'absent' | 'late' | 'excused';

export const ATTENDANCE_STATUSES: AttendanceStatus[] = ['present', 'absent', 'late', 'excused'];

export interface AttendanceRecordRead {
  id: string;
  person_id: string;
  date: string;
  status: AttendanceStatus;
  note: string | null;
}

export interface AttendanceRecordUpsert {
  person_id: string;
  status: AttendanceStatus;
  note?: string | null;
}

/** A whole day in one write - attendance is taken for a group at once. */
export interface AttendanceDayUpsert {
  date: string;
  records: AttendanceRecordUpsert[];
}

export interface AttendanceSummaryRead {
  person_id: string;
  present: number;
  absent: number;
  late: number;
  excused: number;
  total: number;
}
