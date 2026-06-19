import { api } from "@/shared/services/api";
import type {
  AsignacionItem,
  ClonarEquipoPayload,
  OperacionEquipoResult,
} from "@/features/coordinacion/types/coordinacion";

export async function fetchAsignaciones(
  materiaId?: string,
): Promise<AsignacionItem[]> {
  const { data } = await api.get<{ items: AsignacionItem[] }>("/api/asignaciones", {
    params: materiaId ? { materia_id: materiaId } : undefined,
  });
  return data.items;
}

export type CrearAsignacionPayload = {
  usuario_id: string;
  rol: string;
  materia_id?: string;
  carrera_id?: string;
  cohorte_id?: string;
  comisiones?: string[];
  desde: string;
  hasta?: string;
};

export async function crearAsignacion(payload: CrearAsignacionPayload): Promise<AsignacionItem> {
  const { data } = await api.post<AsignacionItem>("/api/asignaciones", payload);
  return data;
}

export async function clonarEquipo(
  payload: ClonarEquipoPayload,
): Promise<OperacionEquipoResult> {
  const { data } = await api.post<OperacionEquipoResult>("/api/equipos/clonar", payload);
  return data;
}

export async function exportarEquipoCsv(
  materiaId: string,
  carreraId: string,
  cohorteId: string,
): Promise<Blob> {
  const { data } = await api.get<Blob>("/api/equipos/exportar", {
    params: {
      materia_id: materiaId,
      carrera_id: carreraId,
      cohorte_id: cohorteId,
    },
    responseType: "blob",
  });
  return data;
}
