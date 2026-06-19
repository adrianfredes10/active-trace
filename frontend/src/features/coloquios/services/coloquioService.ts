import type {
  ConvocatoriaMetricas,
  MetricasGlobales,
  ReservaColoquio,
  ResultadoColoquio,
} from "@/features/coloquios/types/coloquios";
import { api } from "@/shared/services/api";

export async function fetchConvocatorias(): Promise<ConvocatoriaMetricas[]> {
  const { data } = await api.get<{ items: ConvocatoriaMetricas[] }>(
    "/api/coloquios/convocatorias",
  );
  return data.items;
}

export async function fetchMetricasGlobales(): Promise<MetricasGlobales> {
  const { data } = await api.get<MetricasGlobales>("/api/coloquios/metricas");
  return data;
}

export async function fetchConvocatoriaDetalle(
  evaluacionId: string,
): Promise<ConvocatoriaMetricas> {
  const { data } = await api.get<ConvocatoriaMetricas>(
    `/api/coloquios/convocatorias/${evaluacionId}`,
  );
  return data;
}

export async function crearConvocatoria(payload: {
  materia_id: string;
  cohorte_id: string;
  instancia: string;
  tipo?: string;
  dias_disponibles?: number;
  turnos: { fecha: string; hora: string; cupo_max: number }[];
}): Promise<{ id: string }> {
  const { data } = await api.post<{ id: string }>("/api/coloquios/convocatorias", {
    tipo: "coloquio",
    dias_disponibles: 0,
    ...payload,
  });
  return data;
}

export async function cerrarConvocatoria(
  evaluacionId: string,
): Promise<ConvocatoriaMetricas> {
  const { data } = await api.patch<ConvocatoriaMetricas>(
    `/api/coloquios/convocatorias/${evaluacionId}/cerrar`,
  );
  return data;
}

export async function fetchAgendaColoquios(): Promise<ReservaColoquio[]> {
  const { data } = await api.get<{ items: ReservaColoquio[] }>("/api/coloquios/admin/agenda");
  return data.items;
}

export async function fetchResultadosColoquios(): Promise<ResultadoColoquio[]> {
  const { data } = await api.get<{ items: ResultadoColoquio[] }>("/api/coloquios/resultados");
  return data.items;
}

export async function registrarResultado(
  evaluacionId: string,
  payload: { alumno_id: string; nota_final: string },
): Promise<ResultadoColoquio> {
  const { data } = await api.post<ResultadoColoquio>(
    `/api/coloquios/convocatorias/${evaluacionId}/resultados`,
    payload,
  );
  return data;
}
