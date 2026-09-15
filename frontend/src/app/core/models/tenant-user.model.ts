export interface TenantUserRead {
  id: string;
  tenant_id: string;
  email: string;
  is_active: boolean;
}

export interface TenantUserCreate {
  email: string;
  password: string;
}

export interface TenantLoginRequest {
  email: string;
  password: string;
}

export interface TenantTokenResponse {
  access_token: string;
  token_type: string;
}

export interface TenantContextRead {
  id: string;
  name: string;
  slug: string;
}

export interface TenantMeRead {
  user: TenantUserRead;
  tenant: TenantContextRead;
}

export interface HeroFeatureRead {
  key: string;
  name: string;
  description: string | null;
}

export interface TenantLoginContextRead {
  tenant: TenantContextRead;
  hero_features: HeroFeatureRead[];
}
