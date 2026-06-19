import { api } from "@/shared/services/api";

export type ResumenAcademico = {
  total_alumnos: number;
  total_calificaciones: number;
  entregas_aprobadas: number;
  entregas_pendientes: number;
  total_materias: number;
  total_carreras: number;
  total_cohortes: number;
  por_comision: { comision: string; total: number }[];
};

export async function fetchResumenAcademico(): Promise<ResumenAcademico> {
  const { data } = await api.get<ResumenAcademico>("/api/admin/resumen-academico");
  return data;
}
