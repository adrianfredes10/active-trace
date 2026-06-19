import { api } from "@/shared/services/api";
import type { UsuarioAdminItem } from "@/features/admin/types/admin";

export type CrearUsuarioAdminPayload = {
  email: string;
  password: string;
  nombre?: string;
  apellidos?: string;
  banco?: string;
  regional?: string;
  legajo?: string;
  legajo_profesional?: string;
  facturador?: boolean;
};

export type ActualizarUsuarioAdminPayload = {
  nombre?: string;
  apellidos?: string;
  banco?: string;
  regional?: string;
  legajo?: string;
  legajo_profesional?: string;
  facturador?: boolean;
};

export async function fetchUsuariosAdmin(): Promise<UsuarioAdminItem[]> {
  const { data } = await api.get<{ items: UsuarioAdminItem[] }>("/api/admin/usuarios");
  return data.items;
}

export async function crearUsuarioAdmin(
  payload: CrearUsuarioAdminPayload,
): Promise<UsuarioAdminItem> {
  const { data } = await api.post<UsuarioAdminItem>("/api/admin/usuarios", payload);
  return data;
}

export async function actualizarUsuarioAdmin(
  id: string,
  payload: ActualizarUsuarioAdminPayload,
): Promise<UsuarioAdminItem> {
  const { data } = await api.put<UsuarioAdminItem>(`/api/admin/usuarios/${id}`, payload);
  return data;
}

export async function desactivarUsuarioAdmin(id: string): Promise<void> {
  await api.delete(`/api/admin/usuarios/${id}`);
}
