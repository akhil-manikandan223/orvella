export interface DepartmentCreate {
  name: string;
  description?: string | null;
}

export interface DepartmentUpdate {
  name?: string;
  description?: string | null;
}

export interface DepartmentRead {
  id: string;
  tenant_id: string;
  name: string;
  description: string | null;
}

export interface LocationCreate {
  name: string;
  address?: string | null;
}

export interface LocationUpdate {
  name?: string;
  address?: string | null;
}

export interface LocationRead {
  id: string;
  tenant_id: string;
  name: string;
  address: string | null;
}

export interface PersonCreate {
  first_name: string;
  last_name: string;
  category: string;
  email?: string | null;
  phone?: string | null;
  department_id?: string | null;
  location_id?: string | null;
}

export interface PersonUpdate {
  first_name?: string;
  last_name?: string;
  category?: string;
  email?: string | null;
  phone?: string | null;
  department_id?: string | null;
  location_id?: string | null;
}

export interface PersonRead {
  id: string;
  tenant_id: string;
  first_name: string;
  last_name: string;
  email: string | null;
  phone: string | null;
  category: string;
  department_id: string | null;
  location_id: string | null;
  tenant_user_id: string | null;
}
