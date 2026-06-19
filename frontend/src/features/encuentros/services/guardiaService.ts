import type { GuardiaItem } from "@/features/encuentros/types/encuentros";
import { api } from "@/shared/services/api";

export async function fetchGuardias(params?: {
  materia_id?: string;
  cohorte_id?: string;
  asignacion_id?: string;
}): Promise<GuardiaItem[]> {
  const { data } = await api.get<{ items: GuardiaItem[] }>("/api/guardias", { params });
  return data.items;
}

export async function crearGuardia(payload: {
  asignacion_id: string;
  materia_id: string;
  carrera_id: string;
  cohorte_id: string;
  dia: string;
  horario: string;
  comentarios?: string;
}): Promise<GuardiaItem> {
  const { data } = await api.post<GuardiaItem>("/api/guardias", payload);
  return data;
}

export async function actualizarGuardia(
  guardiaId: string,
  payload: { estado?: string; comentarios?: string },
): Promise<GuardiaItem> {
  const { data } = await api.patch<GuardiaItem>(`/api/guardias/${guardiaId}`, payload);
  return data;
}

export async function exportarGuardiasCsv(params?: {
  materia_id?: string;
  cohorte_id?: string;
}): Promise<Blob> {
  const { data } = await api.get<Blob>("/api/guardias/export", {
    params,
    responseType: "blob",
  });
  return data;
}
