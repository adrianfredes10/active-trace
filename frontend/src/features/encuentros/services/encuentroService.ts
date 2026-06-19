import type { InstanciaEncuentro } from "@/features/encuentros/types/encuentros";
import { api } from "@/shared/services/api";

export async function fetchEncuentrosAdmin(): Promise<InstanciaEncuentro[]> {
  const { data } = await api.get<{ items: InstanciaEncuentro[] }>("/api/encuentros/admin");
  return data.items;
}

export async function fetchEncuentrosPorMateria(
  materiaId: string,
  desde?: string,
): Promise<InstanciaEncuentro[]> {
  const { data } = await api.get<{ items: InstanciaEncuentro[] }>("/api/encuentros/instancias", {
    params: { materia_id: materiaId, desde },
  });
  return data.items;
}

export async function crearEncuentroUnico(payload: {
  asignacion_id: string;
  materia_id: string;
  titulo: string;
  fecha: string;
  hora: string;
  meet_url?: string;
}): Promise<InstanciaEncuentro> {
  const { data } = await api.post<InstanciaEncuentro>("/api/encuentros/unico", payload);
  return data;
}

export async function crearEncuentroRecurrente(payload: {
  asignacion_id: string;
  materia_id: string;
  titulo: string;
  hora: string;
  dia_semana: string;
  fecha_inicio: string;
  cant_semanas: number;
  vig_desde: string;
  vig_hasta?: string;
  meet_url?: string;
}): Promise<{ id: string; instancias_generadas: number }> {
  const { data } = await api.post<{ id: string; instancias_generadas: number }>(
    "/api/encuentros/recurrente",
    payload,
  );
  return data;
}

export async function actualizarInstancia(
  instanciaId: string,
  payload: {
    estado?: string;
    meet_url?: string;
    video_url?: string;
    comentario?: string;
  },
): Promise<InstanciaEncuentro> {
  const { data } = await api.patch<InstanciaEncuentro>(
    `/api/encuentros/instancias/${instanciaId}`,
    payload,
  );
  return data;
}

export async function fetchHtmlEncuentros(materiaId: string): Promise<string> {
  const { data } = await api.get<{ html: string }>(`/api/encuentros/html/${materiaId}`);
  return data.html;
}
