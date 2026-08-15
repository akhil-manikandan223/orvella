export interface CountryCreate {
  name: string;
  slug: string;
}

export interface CountryUpdate {
  name?: string;
  slug?: string;
}

export interface CountryRead {
  id: string;
  name: string;
  slug: string;
}

export interface StateCreate {
  country_id: string;
  name: string;
  slug: string;
}

export interface StateUpdate {
  name?: string;
  slug?: string;
}

export interface StateRead {
  id: string;
  country_id: string;
  name: string;
  slug: string;
}

export interface DistrictCreate {
  state_id: string;
  name: string;
  slug: string;
}

export interface DistrictUpdate {
  name?: string;
  slug?: string;
}

export interface DistrictRead {
  id: string;
  state_id: string;
  name: string;
  slug: string;
}

export interface CityCreate {
  state_id: string;
  district_id?: string | null;
  name: string;
  slug: string;
}

export interface CityUpdate {
  district_id?: string | null;
  name?: string;
  slug?: string;
}

export interface CityRead {
  id: string;
  state_id: string;
  district_id: string | null;
  name: string;
  slug: string;
}
