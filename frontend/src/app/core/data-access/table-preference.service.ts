import { Service, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { TableColumnPreferenceRead, TableColumnPreferenceUpsert } from '../models/table-preference.model';

const BASE_URL = `${environment.apiUrl}/platform-admin/table-preferences`;

@Service()
export class TablePreferenceService {
  private readonly http = inject(HttpClient);

  get(tableKey: string): Observable<TableColumnPreferenceRead | null> {
    return this.http.get<TableColumnPreferenceRead | null>(`${BASE_URL}/${tableKey}`);
  }

  save(tableKey: string, payload: TableColumnPreferenceUpsert): Observable<TableColumnPreferenceRead> {
    return this.http.put<TableColumnPreferenceRead>(`${BASE_URL}/${tableKey}`, payload);
  }
}
