import { Service, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import {
  TenantCreate,
  TenantDetailRead,
  TenantFeatureRead,
  TenantFeatureToggleRequest,
  TenantRead,
  TenantUpdate,
} from '../models/tenant.model';

const BASE_URL = `${environment.apiUrl}/platform-admin/tenants`;

@Service()
export class TenantService {
  private readonly http = inject(HttpClient);

  list(): Observable<TenantRead[]> {
    return this.http.get<TenantRead[]>(BASE_URL);
  }

  get(id: string): Observable<TenantDetailRead> {
    return this.http.get<TenantDetailRead>(`${BASE_URL}/${id}`);
  }

  create(payload: TenantCreate): Observable<TenantDetailRead> {
    return this.http.post<TenantDetailRead>(BASE_URL, payload);
  }

  update(id: string, payload: TenantUpdate): Observable<TenantRead> {
    return this.http.patch<TenantRead>(`${BASE_URL}/${id}`, payload);
  }

  toggleFeature(
    tenantId: string,
    featureId: string,
    payload: TenantFeatureToggleRequest,
  ): Observable<TenantFeatureRead> {
    return this.http.patch<TenantFeatureRead>(
      `${BASE_URL}/${tenantId}/features/${featureId}`,
      payload,
    );
  }
}
