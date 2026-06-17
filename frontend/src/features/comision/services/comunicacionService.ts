import { api } from "@/shared/services/api";
import type {
  AlumnoAtrasado,
  ComisionContexto,
  ComunicacionEnviarResult,
  ComunicacionPreview,
  LoteComunicacion,
} from "@/features/comision/types/comision";

export async function previewComunicacion(
  asunto: string,
  cuerpo: string,
  muestra: AlumnoAtrasado,
): Promise<ComunicacionPreview> {
  const { data } = await api.post<ComunicacionPreview>("/api/comunicaciones/preview", {
    asunto,
    cuerpo,
    muestra: {
      email: muestra.email,
      nombre: muestra.nombre,
      apellidos: muestra.apellidos,
    },
  });
  return data;
}

export async function enviarComunicacion(
  ctx: ComisionContexto,
  asunto: string,
  cuerpo: string,
  destinatarios: AlumnoAtrasado[],
  confirmoPreview: boolean,
): Promise<ComunicacionEnviarResult> {
  const { data } = await api.post<ComunicacionEnviarResult>("/api/comunicaciones/enviar", {
    materia_id: ctx.materia_id,
    asunto,
    cuerpo,
    destinatarios: destinatarios.map((d) => ({
      email: d.email,
      nombre: d.nombre,
      apellidos: d.apellidos,
    })),
    confirmo_preview: confirmoPreview,
  });
  return data;
}

export async function fetchLote(loteId: string): Promise<LoteComunicacion> {
  const { data } = await api.get<LoteComunicacion>(`/api/comunicaciones/lotes/${loteId}`);
  return data;
}
