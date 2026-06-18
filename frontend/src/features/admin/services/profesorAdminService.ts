import { api } from "@/shared/services/api";
import type { CohorteItem } from "@/features/admin/types/admin";
import type { UsuarioAdminItem } from "@/features/admin/types/admin";

export type CrearProfesorPayload = {
  email: string;
  password: string;
  nombre?: string;
  apellidos?: string;
  materia_id: string;
  carrera_id: string;
  cohorte_id: string;
  comision: string;
};

export type CrearProfesorResult = {
  usuario: UsuarioAdminItem;
  asignacion_id: string;
  comision: string;
};

export async function fetchCohortes(carreraId?: string): Promise<CohorteItem[]> {
  const { data } = await api.get<{ items: CohorteItem[] }>("/api/admin/cohortes", {
    params: carreraId ? { carrera_id: carreraId } : undefined,
  });
  return data.items;
}

export async function crearProfesorCompleto(
  payload: CrearProfesorPayload,
): Promise<CrearProfesorResult> {
  const { data } = await api.post<CrearProfesorResult>("/api/admin/usuarios/profesor", payload);
  return data;
}
