import { Service, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { CountryCreate, CountryRead, CountryUpdate } from '../models/geo.model';

const BASE_URL = `${environment.apiUrl}/platform-admin/countries`;

@Service()
export class CountryService {
  private readonly http = inject(HttpClient);

  list(): Observable<CountryRead[]> {
    return this.http.get<CountryRead[]>(BASE_URL);
  }

  create(payload: CountryCreate): Observable<CountryRead> {
    return this.http.post<CountryRead>(BASE_URL, payload);
  }

  update(id: string, payload: CountryUpdate): Observable<CountryRead> {
    return this.http.patch<CountryRead>(`${BASE_URL}/${id}`, payload);
  }
}
