export type InstanciaEncuentro = {
  id: string;
  slot_id: string | null;
  materia_id: string;
  fecha: string;
  hora: string;
  titulo: string;
  estado: string;
  meet_url: string | null;
  video_url: string | null;
  comentario: string | null;
};

export type GuardiaItem = {
  id: string;
  asignacion_id: string;
  materia_id: string;
  carrera_id: string;
  cohorte_id: string;
  dia: string;
  horario: string;
  estado: string;
  comentarios: string | null;
  creada_at: string;
};

export const DIAS_SEMANA = [
  "Lunes",
  "Martes",
  "Miércoles",
  "Jueves",
  "Viernes",
  "Sábado",
  "Domingo",
] as const;

export type DiaSemana = (typeof DIAS_SEMANA)[number];
