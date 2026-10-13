import { Service, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { GroupCreate, GroupDetailRead, GroupRead, GroupUpdate } from '../models/group.model';

const BASE_URL = `${environment.apiUrl}/tenant/groups`;

@Service()
export class GroupService {
  private readonly http = inject(HttpClient);

  list(): Observable<GroupRead[]> {
    return this.http.get<GroupRead[]>(BASE_URL);
  }

  /** The groups the signed-in user personally supervises, with their rosters -
   * what a homeroom teacher's attendance sheet is built from. */
  supervised(): Observable<GroupDetailRead[]> {
    return this.http.get<GroupDetailRead[]>(`${BASE_URL}/supervised`);
  }

  get(id: string): Observable<GroupDetailRead> {
    return this.http.get<GroupDetailRead>(`${BASE_URL}/${id}`);
  }

  create(payload: GroupCreate): Observable<GroupRead> {
    return this.http.post<GroupRead>(BASE_URL, payload);
  }

  update(id: string, payload: GroupUpdate): Observable<GroupRead> {
    return this.http.patch<GroupRead>(`${BASE_URL}/${id}`, payload);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${BASE_URL}/${id}`);
  }

  /** PUT, not POST: the body is the whole roster, not an addition to it. */
  setMembers(id: string, personIds: string[]): Observable<string[]> {
    return this.http.put<string[]>(`${BASE_URL}/${id}/members`, { person_ids: personIds });
  }

  setSupervisors(id: string, tenantUserIds: string[]): Observable<string[]> {
    return this.http.put<string[]>(`${BASE_URL}/${id}/supervisors`, {
      tenant_user_ids: tenantUserIds,
    });
  }
}
