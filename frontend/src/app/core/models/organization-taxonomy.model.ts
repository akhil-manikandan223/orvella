export interface OrganizationCategoryCreate {
  name: string;
  slug: string;
}

export interface OrganizationCategoryUpdate {
  name?: string;
  slug?: string;
}

export interface OrganizationCategoryRead {
  id: string;
  name: string;
  slug: string;
}

export interface OrganizationTypeCreate {
  organization_category_id: string;
  name: string;
  slug: string;
}

export interface OrganizationTypeUpdate {
  name?: string;
  slug?: string;
}

export interface OrganizationTypeRead {
  id: string;
  organization_category_id: string;
  name: string;
  slug: string;
}
