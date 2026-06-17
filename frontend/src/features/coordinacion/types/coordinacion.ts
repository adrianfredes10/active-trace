import type { AsignacionItem } from "@/features/comision/types/comision";

export type { AsignacionItem };

export type ComisionContexto = {
  asignacion_id: string;
  materia_id: string;
  cohorte_id: string;
  carrera_id: string;
};

export type OperacionEquipoResult = {
  creadas: number;
  actualizadas: number;
  items: AsignacionItem[];
};

export type ClonarEquipoPayload = {
  origen: { materia_id: string; carrera_id: string; cohorte_id: string };
  destino: { materia_id: string; carrera_id: string; cohorte_id: string };
  desde: string;
  hasta?: string | null;
};

export type AvisoItem = {
  id: string;
  alcance: string;
  materia_id: string | null;
  cohorte_id: string | null;
  rol_destino: string | null;
  severidad: string;
  titulo: string;
  cuerpo: string;
  inicio_en: string;
  fin_en: string | null;
  orden: number;
  activo: boolean;
  requiere_ack: boolean;
};

export type AvisoCreatePayload = {
  alcance: string;
  materia_id?: string | null;
  cohorte_id?: string | null;
  rol_destino?: string | null;
  severidad: string;
  titulo: string;
  cuerpo: string;
  inicio_en: string;
  fin_en?: string | null;
  orden?: number;
  requiere_ack?: boolean;
};

export type TareaItem = {
  id: string;
  materia_id: string | null;
  asignado_a: string;
  asignado_por: string;
  estado: string;
  descripcion: string;
  contexto_id: string | null;
};

export type MonitorAlumno = {
  entrada_padron_id: string;
  email: string;
  nombre: string;
  apellidos: string;
  comision: string | null;
  regional: string | null;
  aprobadas: number;
  total_actividades: number;
  atrasado: boolean;
};
