import { Service, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { CityCreate, CityRead, CityUpdate } from '../models/geo.model';

const BASE_URL = `${environment.apiUrl}/platform-admin/cities`;

@Service()
export class CityService {
  private readonly http = inject(HttpClient);

  list(stateId?: string, districtId?: string): Observable<CityRead[]> {
    let params = new HttpParams();
    if (stateId) {
      params = params.set('state_id', stateId);
    }
    if (districtId) {
      params = params.set('district_id', districtId);
    }
    return this.http.get<CityRead[]>(BASE_URL, { params });
  }

  create(payload: CityCreate): Observable<CityRead> {
    return this.http.post<CityRead>(BASE_URL, payload);
  }

  update(id: string, payload: CityUpdate): Observable<CityRead> {
    return this.http.patch<CityRead>(`${BASE_URL}/${id}`, payload);
  }
}
