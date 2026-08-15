export type FeatureStatus = 'active' | 'deprecated';

export interface FeatureCreate {
  key: string;
  name: string;
  description?: string | null;
  status?: FeatureStatus;
}

export interface FeatureUpdate {
  name?: string;
  description?: string | null;
  status?: FeatureStatus;
}

export interface FeatureRead {
  id: string;
  key: string;
  name: string;
  description: string | null;
  status: FeatureStatus;
}
