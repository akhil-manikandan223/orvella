import { Service, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { PersonCreate, PersonRead, PersonUpdate } from '../models/organization.model';

const BASE_URL = `${environment.apiUrl}/tenant/people`;

@Service()
export class PersonService {
  private readonly http = inject(HttpClient);

  list(): Observable<PersonRead[]> {
    return this.http.get<PersonRead[]>(BASE_URL);
  }

  create(payload: PersonCreate): Observable<PersonRead> {
    return this.http.post<PersonRead>(BASE_URL, payload);
  }

  update(id: string, payload: PersonUpdate): Observable<PersonRead> {
    return this.http.patch<PersonRead>(`${BASE_URL}/${id}`, payload);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${BASE_URL}/${id}`);
  }
}
