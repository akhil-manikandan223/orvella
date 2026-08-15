export interface AuditLogRead {
  id: string;
  actor_type: string | null;
  actor_id: string | null;
  action: string;
  entity_type: string;
  entity_id: string;
  tenant_id: string | null;
  changes: Record<string, unknown>;
  created_at: string;
}
