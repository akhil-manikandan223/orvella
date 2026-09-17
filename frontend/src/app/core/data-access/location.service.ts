import { Service, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { LocationCreate, LocationRead, LocationUpdate } from '../models/organization.model';

const BASE_URL = `${environment.apiUrl}/tenant/locations`;

@Service()
export class LocationService {
  private readonly http = inject(HttpClient);

  list(): Observable<LocationRead[]> {
    return this.http.get<LocationRead[]>(BASE_URL);
  }

  create(payload: LocationCreate): Observable<LocationRead> {
    return this.http.post<LocationRead>(BASE_URL, payload);
  }

  update(id: string, payload: LocationUpdate): Observable<LocationRead> {
    return this.http.patch<LocationRead>(`${BASE_URL}/${id}`, payload);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${BASE_URL}/${id}`);
  }
}
