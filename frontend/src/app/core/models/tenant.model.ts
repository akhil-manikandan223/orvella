import { FeatureRead } from './feature.model';

export interface TenantCreate {
  name: string;
  slug: string;
  organization_type_id: string;
  max_users?: number | null;

  address_line_1: string;
  address_line_2?: string | null;
  country_id: string;
  state_id?: string | null;
  city_id: string;
  postal_code?: string | null;
  license_number: string;
  logo_url?: string | null;
  key_contact_name: string;
  key_contact_email: string;
  key_contact_phone: string;
}

export interface TenantUpdate {
  max_users?: number | null;
  is_active?: boolean;

  address_line_1?: string;
  address_line_2?: string | null;
  country_id?: string;
  state_id?: string | null;
  city_id?: string;
  postal_code?: string | null;
  license_number?: string;
  logo_url?: string | null;
  key_contact_name?: string;
  key_contact_email?: string;
  key_contact_phone?: string;
}

export interface TenantRead {
  id: string;
  name: string;
  slug: string;
  organization_type_id: string;
  max_users: number | null;
  is_active: boolean;

  address_line_1: string;
  address_line_2: string | null;
  country_id: string;
  state_id: string | null;
  city_id: string;
  postal_code: string | null;
  license_number: string;
  logo_url: string | null;
  key_contact_name: string;
  key_contact_email: string;
  key_contact_phone: string;
}

export interface TenantDetailRead extends TenantRead {
  features: FeatureRead[];
}

export interface TenantFeatureToggleRequest {
  enabled: boolean;
}

export interface TenantFeatureRead {
  feature_id: string;
  enabled: boolean;
}
