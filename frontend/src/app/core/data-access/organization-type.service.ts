import { Service, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { FeatureRead } from '../models/feature.model';
import {
  OrganizationTypeCreate,
  OrganizationTypeRead,
  OrganizationTypeUpdate,
} from '../models/organization-taxonomy.model';

const BASE_URL = `${environment.apiUrl}/platform-admin/organization-types`;

@Service()
export class OrganizationTypeService {
  private readonly http = inject(HttpClient);

  list(organizationCategoryId?: string): Observable<OrganizationTypeRead[]> {
    const params = organizationCategoryId
      ? new HttpParams().set('organization_category_id', organizationCategoryId)
      : undefined;
    return this.http.get<OrganizationTypeRead[]>(BASE_URL, { params });
  }

  create(payload: OrganizationTypeCreate): Observable<OrganizationTypeRead> {
    return this.http.post<OrganizationTypeRead>(BASE_URL, payload);
  }

  update(id: string, payload: OrganizationTypeUpdate): Observable<OrganizationTypeRead> {
    return this.http.patch<OrganizationTypeRead>(`${BASE_URL}/${id}`, payload);
  }

  listTemplateFeatures(organizationTypeId: string): Observable<FeatureRead[]> {
    return this.http.get<FeatureRead[]>(`${BASE_URL}/${organizationTypeId}/features`);
  }

  attachTemplateFeature(organizationTypeId: string, featureId: string): Observable<void> {
    return this.http.post<void>(`${BASE_URL}/${organizationTypeId}/features/${featureId}`, null);
  }

  detachTemplateFeature(organizationTypeId: string, featureId: string): Observable<void> {
    return this.http.delete<void>(`${BASE_URL}/${organizationTypeId}/features/${featureId}`);
  }
}
