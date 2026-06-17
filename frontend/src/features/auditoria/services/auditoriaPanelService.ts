import { api } from "@/shared/services/api";
import type { AuditLogItem } from "@/features/auditoria/types/audit";

export type AccionPorDia = { dia: string; accion: string; total: number };
export type ComunicacionEstado = { enviado_por: string; estado: string; total: number };
export type InteraccionItem = {
  actor_id: string;
  materia_id: string | null;
  accion: string;
  total: number;
};

export async function fetchAccionesPorDia(
  desde?: string,
  hasta?: string,
): Promise<AccionPorDia[]> {
  const { data } = await api.get<{ items: AccionPorDia[] }>(
    "/api/auditoria/panel/acciones-por-dia",
    { params: { desde, hasta } },
  );
  return data.items;
}

export async function fetchComunicacionesPorDocente(): Promise<ComunicacionEstado[]> {
  const { data } = await api.get<{ items: ComunicacionEstado[] }>(
    "/api/auditoria/panel/comunicaciones-por-docente",
  );
  return data.items;
}

export async function fetchInteracciones(
  desde?: string,
  hasta?: string,
): Promise<InteraccionItem[]> {
  const { data } = await api.get<{ items: InteraccionItem[] }>(
    "/api/auditoria/panel/interacciones",
    { params: { desde, hasta } },
  );
  return data.items;
}

export type AuditoriaLogFiltros = {
  materia_id?: string;
  usuario_id?: string;
  accion?: string;
  limit?: number;
};

export async function fetchAuditoriaLog(
  filtros: AuditoriaLogFiltros,
): Promise<{ items: AuditLogItem[]; limit: number }> {
  const { data } = await api.get<{ items: AuditLogItem[]; limit: number }>(
    "/api/auditoria/log",
    { params: filtros },
  );
  return data;
}
