import { api } from "@/shared/services/api";
import type {
  AtrasadosResponse,
  ComisionContexto,
  RankingItem,
  ReporteRapido,
} from "@/features/comision/types/comision";

function ctxParams(ctx: ComisionContexto) {
  return {
    asignacion_id: ctx.asignacion_id,
    materia_id: ctx.materia_id,
    cohorte_id: ctx.cohorte_id,
    ...(ctx.comision ? { comision: ctx.comision } : {}),
  };
}

export async function fetchAtrasados(ctx: ComisionContexto): Promise<AtrasadosResponse> {
  const { data } = await api.get<AtrasadosResponse>("/api/analisis/atrasados", {
    params: ctxParams(ctx),
  });
  return data;
}

export async function fetchRanking(ctx: ComisionContexto): Promise<RankingItem[]> {
  const { data } = await api.get<{ items: RankingItem[] }>("/api/analisis/ranking", {
    params: ctxParams(ctx),
  });
  return data.items;
}

export async function fetchReporteRapido(ctx: ComisionContexto): Promise<ReporteRapido> {
  const { data } = await api.get<ReporteRapido>("/api/analisis/reporte-rapido", {
    params: ctxParams(ctx),
  });
  return data;
}

export async function exportSinCorregir(ctx: ComisionContexto): Promise<Blob> {
  const { data } = await api.get<Blob>("/api/analisis/sin-corregir/export", {
    params: ctxParams(ctx),
    responseType: "blob",
  });
  return data;
}
