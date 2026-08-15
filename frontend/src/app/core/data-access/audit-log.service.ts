import { Service, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { AuditLogRead } from '../models/audit-log.model';

const BASE_URL = `${environment.apiUrl}/platform-admin/audit-logs`;

export interface AuditLogFilters {
  entityType?: string;
  entityId?: string;
  tenantId?: string;
}

@Service()
export class AuditLogService {
  private readonly http = inject(HttpClient);

  list(filters: AuditLogFilters = {}): Observable<AuditLogRead[]> {
    let params = new HttpParams();
    if (filters.entityType) {
      params = params.set('entity_type', filters.entityType);
    }
    if (filters.entityId) {
      params = params.set('entity_id', filters.entityId);
    }
    if (filters.tenantId) {
      params = params.set('tenant_id', filters.tenantId);
    }
    return this.http.get<AuditLogRead[]>(BASE_URL, { params });
  }
}
