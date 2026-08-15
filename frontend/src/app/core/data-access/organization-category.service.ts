import { Service, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import {
  OrganizationCategoryCreate,
  OrganizationCategoryRead,
  OrganizationCategoryUpdate,
} from '../models/organization-taxonomy.model';

const BASE_URL = `${environment.apiUrl}/platform-admin/organization-categories`;

@Service()
export class OrganizationCategoryService {
  private readonly http = inject(HttpClient);

  list(): Observable<OrganizationCategoryRead[]> {
    return this.http.get<OrganizationCategoryRead[]>(BASE_URL);
  }

  create(payload: OrganizationCategoryCreate): Observable<OrganizationCategoryRead> {
    return this.http.post<OrganizationCategoryRead>(BASE_URL, payload);
  }

  update(id: string, payload: OrganizationCategoryUpdate): Observable<OrganizationCategoryRead> {
    return this.http.patch<OrganizationCategoryRead>(`${BASE_URL}/${id}`, payload);
  }
}
