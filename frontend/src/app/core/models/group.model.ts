/** A set of people with someone responsible for them - a class, a batch, a
 * ward, a team. Deliberately not called "Class": the same primitive has to
 * fit every kind of organization Orvella serves. */
export interface GroupRead {
  id: string;
  tenant_id: string;
  name: string;
  description: string | null;
  department_id: string | null;
}

export interface GroupDetailRead extends GroupRead {
  member_ids: string[];
  /** Tenant users who may mark this group's attendance. */
  supervisor_ids: string[];
}

export interface GroupCreate {
  name: string;
  description?: string | null;
  department_id?: string | null;
}

export interface GroupUpdate {
  name?: string;
  description?: string | null;
  department_id?: string | null;
}
