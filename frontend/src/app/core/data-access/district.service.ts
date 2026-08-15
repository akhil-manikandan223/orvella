import { Service, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { DistrictCreate, DistrictRead, DistrictUpdate } from '../models/geo.model';

const BASE_URL = `${environment.apiUrl}/platform-admin/districts`;

@Service()
export class DistrictService {
  private readonly http = inject(HttpClient);

  list(stateId?: string): Observable<DistrictRead[]> {
    const params = stateId ? new HttpParams().set('state_id', stateId) : undefined;
    return this.http.get<DistrictRead[]>(BASE_URL, { params });
  }

  create(payload: DistrictCreate): Observable<DistrictRead> {
    return this.http.post<DistrictRead>(BASE_URL, payload);
  }

  update(id: string, payload: DistrictUpdate): Observable<DistrictRead> {
    return this.http.patch<DistrictRead>(`${BASE_URL}/${id}`, payload);
  }
}
