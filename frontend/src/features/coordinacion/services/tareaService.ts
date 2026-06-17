import { api } from "@/shared/services/api";
import type { TareaItem } from "@/features/coordinacion/types/coordinacion";

export async function fetchTareasAdmin(materiaId?: string): Promise<TareaItem[]> {
  const { data } = await api.get<{ items: TareaItem[] }>("/api/tareas/admin", {
    params: materiaId ? { materia_id: materiaId } : undefined,
  });
  return data.items;
}

export async function crearTarea(payload: {
  asignado_a: string;
  descripcion: string;
  materia_id?: string | null;
}): Promise<TareaItem> {
  const { data } = await api.post<TareaItem>("/api/tareas", payload);
  return data;
}

export async function actualizarEstadoTarea(
  tareaId: string,
  estado: string,
): Promise<TareaItem> {
  const { data } = await api.patch<TareaItem>(`/api/tareas/${tareaId}/estado`, { estado });
  return data;
}
