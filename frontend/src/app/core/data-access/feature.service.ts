import { Service, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { FeatureCreate, FeatureRead, FeatureUpdate } from '../models/feature.model';

const BASE_URL = `${environment.apiUrl}/platform-admin/features`;

@Service()
export class FeatureService {
  private readonly http = inject(HttpClient);

  list(): Observable<FeatureRead[]> {
    return this.http.get<FeatureRead[]>(BASE_URL);
  }

  create(payload: FeatureCreate): Observable<FeatureRead> {
    return this.http.post<FeatureRead>(BASE_URL, payload);
  }

  update(id: string, payload: FeatureUpdate): Observable<FeatureRead> {
    return this.http.patch<FeatureRead>(`${BASE_URL}/${id}`, payload);
  }
}
