import { api } from "@/shared/services/api";
import type { UsuarioAdminItem } from "@/features/admin/types/admin";

export type CrearUsuarioAdminPayload = {
  email: string;
  password: string;
  nombre?: string;
  apellidos?: string;
  legajo?: string;
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