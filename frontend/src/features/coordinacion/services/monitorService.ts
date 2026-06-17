import { api } from "@/shared/services/api";
import type { MonitorAlumno } from "@/features/coordinacion/types/coordinacion";

export type MonitorFiltros = {
  materia_id: string;
  cohorte_id: string;
  asignacion_id?: string;
  comision?: string;
  email?: string;
  solo_atrasados?: boolean;
};

export async function fetchMonitorGeneral(
  filtros: MonitorFiltros,
): Promise<MonitorAlumno[]> {
  const { data } = await api.get<{ items: MonitorAlumno[] }>("/api/analisis/monitor/general", {
    params: filtros,
  });
  return data.items;
}
