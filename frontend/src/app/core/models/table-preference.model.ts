export interface TableColumnPreferenceRead {
  table_key: string;
  visible_columns: string[];
}

export interface TableColumnPreferenceUpsert {
  visible_columns: string[];
}
