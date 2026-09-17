import { Service, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { TenantUserCreate, TenantUserRead, TenantUserUpdate } from '../models/tenant-user.model';

const BASE_URL = `${environment.apiUrl}/platform-admin/tenants`;

@Service()
export class TenantUserService {
  private readonly http = inject(HttpClient);

  list(tenantId: string): Observable<TenantUserRead[]> {
    return this.http.get<TenantUserRead[]>(`${BASE_URL}/${tenantId}/users`);
  }

  create(tenantId: string, payload: TenantUserCreate): Observable<TenantUserRead> {
    return this.http.post<TenantUserRead>(`${BASE_URL}/${tenantId}/users`, payload);
  }

  update(tenantId: string, userId: string, payload: TenantUserUpdate): Observable<TenantUserRead> {
    return this.http.patch<TenantUserRead>(`${BASE_URL}/${tenantId}/users/${userId}`, payload);
  }
}
