import { api } from "@/shared/services/api";
import type {
  LiquidacionItem,
  LiquidacionKpis,
  LiquidacionSegmento,
  SalarioBaseItem,
} from "@/features/finanzas/types/finanzas";

/** Contrato preparado para C-18 — endpoints aún no implementados en backend. */

export async function fetchLiquidaciones(
  periodo: string,
  segmento: LiquidacionSegmento,
): Promise<LiquidacionItem[]> {
  const { data } = await api.get<{ items: LiquidacionItem[] }>("/api/liquidaciones", {
    params: { periodo, segmento },
  });
  return data.items;
}

export async function fetchLiquidacionKpis(periodo: string): Promise<LiquidacionKpis> {
  const { data } = await api.get<LiquidacionKpis>("/api/liquidaciones/kpis", {
    params: { periodo },
  });
  return data;
}

export async function cerrarLiquidacion(liquidacionId: string): Promise<LiquidacionItem> {
  const { data } = await api.post<LiquidacionItem>(
    `/api/liquidaciones/${liquidacionId}/cerrar`,
  );
  return data;
}

export async function fetchGrillaSalarial(): Promise<SalarioBaseItem[]> {
  const { data } = await api.get<{ items: SalarioBaseItem[] }>("/api/liquidaciones/grilla");
  return data.items;
}

export async function guardarSalarioBase(payload: {
  rol: string;
  monto: string;
  vig_desde: string;
}): Promise<SalarioBaseItem> {
  const { data } = await api.post<SalarioBaseItem>("/api/liquidaciones/grilla/base", payload);
  return data;
}
