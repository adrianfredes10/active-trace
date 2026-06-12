import { api } from "@/shared/services/api";
import type { AuditLogListResponse } from "@/features/auditoria/types/audit";

export async function fetchAuditLogs(limit = 50): Promise<AuditLogListResponse> {
  const { data } = await api.get<AuditLogListResponse>("/api/audit", { params: { limit } });
  return data;
}
