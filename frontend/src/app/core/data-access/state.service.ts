import { Service, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { StateCreate, StateRead, StateUpdate } from '../models/geo.model';

const BASE_URL = `${environment.apiUrl}/platform-admin/states`;

@Service()
export class StateService {
  private readonly http = inject(HttpClient);

  list(countryId?: string): Observable<StateRead[]> {
    const params = countryId ? new HttpParams().set('country_id', countryId) : undefined;
    return this.http.get<StateRead[]>(BASE_URL, { params });
  }

  create(payload: StateCreate): Observable<StateRead> {
    return this.http.post<StateRead>(BASE_URL, payload);
  }

  update(id: string, payload: StateUpdate): Observable<StateRead> {
    return this.http.patch<StateRead>(`${BASE_URL}/${id}`, payload);
  }
}
