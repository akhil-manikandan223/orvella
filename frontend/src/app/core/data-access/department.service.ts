import { Service, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { DepartmentCreate, DepartmentRead, DepartmentUpdate } from '../models/organization.model';

const BASE_URL = `${environment.apiUrl}/tenant/departments`;

@Service()
export class DepartmentService {
  private readonly http = inject(HttpClient);

  list(): Observable<DepartmentRead[]> {
    return this.http.get<DepartmentRead[]>(BASE_URL);
  }

  create(payload: DepartmentCreate): Observable<DepartmentRead> {
    return this.http.post<DepartmentRead>(BASE_URL, payload);
  }

  update(id: string, payload: DepartmentUpdate): Observable<DepartmentRead> {
    return this.http.patch<DepartmentRead>(`${BASE_URL}/${id}`, payload);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${BASE_URL}/${id}`);
  }
}
