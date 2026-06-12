export type AuditLogItem = {
  id: string;
  fecha_hora: string;
  actor_id: string;
  impersonado_id: string | null;
  materia_id: string | null;
  accion: string;
  detalle: Record<string, unknown> | null;
  filas_afectadas: number;
  ip: string | null;
};

export type AuditLogListResponse = {
  items: AuditLogItem[];
};
