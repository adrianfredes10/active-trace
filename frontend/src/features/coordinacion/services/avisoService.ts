import { api } from "@/shared/services/api";
import type { AvisoCreatePayload, AvisoItem } from "@/features/coordinacion/types/coordinacion";

export async function fetchAvisosGestion(): Promise<AvisoItem[]> {
  const { data } = await api.get<{ items: AvisoItem[] }>("/api/avisos");
  return data.items;
}

export async function crearAviso(payload: AvisoCreatePayload): Promise<AvisoItem> {
  const { data } = await api.post<AvisoItem>("/api/avisos", payload);
  return data;
}

export async function eliminarAviso(avisoId: string): Promise<void> {
  await api.delete(`/api/avisos/${avisoId}`);
}
