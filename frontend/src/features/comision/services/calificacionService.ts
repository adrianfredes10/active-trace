import { api } from "@/shared/services/api";
import type {
  CalificacionImportResult,
  CalificacionPreview,
  ComisionContexto,
  UmbralMateria,
} from "@/features/comision/types/comision";

export async function previewCalificaciones(file: File): Promise<CalificacionPreview> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post<CalificacionPreview>("/api/calificaciones/preview", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function importarCalificaciones(
  ctx: ComisionContexto,
  actividades: string[],
  file: File,
): Promise<CalificacionImportResult> {
  const form = new FormData();
  form.append("asignacion_id", ctx.asignacion_id);
  form.append("materia_id", ctx.materia_id);
  form.append("cohorte_id", ctx.cohorte_id);
  form.append("actividades", actividades.join(","));
  form.append("file", file);
  const { data } = await api.post<CalificacionImportResult>(
    "/api/calificaciones/importar",
    form,
    { headers: { "Content-Type": "multipart/form-data" } },
  );
  return data;
}

export async function fetchUmbral(asignacionId: string): Promise<UmbralMateria | null> {
  try {
    const { data } = await api.get<UmbralMateria>(`/api/calificaciones/umbral/${asignacionId}`);
    return data;
  } catch {
    return null;
  }
}

export async function guardarUmbral(
  ctx: ComisionContexto,
  umbralPct: number,
  valoresAprobatorios: string[],
): Promise<UmbralMateria> {
  const { data } = await api.put<UmbralMateria>("/api/calificaciones/umbral", {
    asignacion_id: ctx.asignacion_id,
    materia_id: ctx.materia_id,
    umbral_pct: umbralPct,
    valores_aprobatorios: valoresAprobatorios,
  });
  return data;
}
