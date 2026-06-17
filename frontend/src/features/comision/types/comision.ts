export type AsignacionItem = {
  id: string;
  usuario_id: string;
  rol: string;
  materia_id: string | null;
  carrera_id: string | null;
  cohorte_id: string | null;
  comisiones: string[];
  vigente: boolean;
  desde: string;
  hasta: string | null;
  materia_codigo?: string | null;
  materia_nombre?: string | null;
  cohorte_nombre?: string | null;
  carrera_codigo?: string | null;
};

export type EquipoListResponse = {
  items: AsignacionItem[];
};

export type ActividadDetectada = {
  nombre: string;
  tipo: string;
};

export type CalificacionPreview = {
  actividades: ActividadDetectada[];
  total_filas: number;
  muestra_emails: string[];
};

export type CalificacionImportResult = {
  importadas: number;
};

export type UmbralMateria = {
  id: string;
  asignacion_id: string;
  materia_id: string;
  umbral_pct: number;
  valores_aprobatorios: string[];
};

export type AlumnoAtrasado = {
  entrada_padron_id: string;
  email: string;
  nombre: string;
  apellidos: string;
  comision: string | null;
  motivos: string[];
};

export type AtrasadosResponse = {
  total_alumnos: number;
  total_atrasados: number;
  items: AlumnoAtrasado[];
};

export type RankingItem = {
  entrada_padron_id: string;
  email: string;
  nombre: string;
  apellidos: string;
  aprobadas: number;
};

export type ReporteRapido = {
  total_alumnos: number;
  total_atrasados: number;
  total_actividades: number;
  tasa_aprobacion_pct: string | null;
};

export type ComunicacionPreview = {
  asunto: string;
  cuerpo: string;
};

export type ComunicacionItem = {
  id: string;
  materia_id: string;
  asunto: string;
  estado: string;
  lote_id: string;
  es_masivo: boolean;
  aprobado: boolean;
  enviado_at: string | null;
};

export type ComunicacionEnviarResult = {
  lote_id: string;
  encoladas: number;
  requiere_aprobacion: boolean;
  items: ComunicacionItem[];
};

export type LoteComunicacion = {
  lote_id: string;
  total: number;
  items: ComunicacionItem[];
};

export type ComisionContexto = {
  asignacion_id: string;
  materia_id: string;
  cohorte_id: string;
};
