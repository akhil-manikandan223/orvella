import { Service, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import {
  AttendanceDayUpsert,
  AttendanceRecordRead,
  AttendanceSummaryRead,
} from '../models/attendance.model';

const BASE_URL = `${environment.apiUrl}/tenant/attendance`;

@Service()
export class AttendanceService {
  private readonly http = inject(HttpClient);

  listForDate(date: string): Observable<AttendanceRecordRead[]> {
    return this.http.get<AttendanceRecordRead[]>(BASE_URL, {
      params: new HttpParams().set('date', date),
    });
  }

  listAbsentees(date: string): Observable<AttendanceRecordRead[]> {
    return this.http.get<AttendanceRecordRead[]>(`${BASE_URL}/absentees`, {
      params: new HttpParams().set('date', date),
    });
  }

  summary(start: string, end: string): Observable<AttendanceSummaryRead[]> {
    return this.http.get<AttendanceSummaryRead[]>(`${BASE_URL}/summary`, {
      params: new HttpParams().set('start', start).set('end', end),
    });
  }

  /** PUT, not POST: re-saving a day corrects it rather than duplicating it. */
  markDay(payload: AttendanceDayUpsert): Observable<AttendanceRecordRead[]> {
    return this.http.put<AttendanceRecordRead[]>(BASE_URL, payload);
  }
}
