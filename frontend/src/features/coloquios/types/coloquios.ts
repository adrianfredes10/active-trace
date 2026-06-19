export type ConvocatoriaMetricas = {
  evaluacion_id: string;
  materia_id: string;
  cohorte_id: string;
  instancia: string;
  tipo: string;
  estado: string;
  convocados: number;
  reservas_activas: number;
  cupos_libres: number;
  notas_registradas: number;
};

export type MetricasGlobales = {
  convocados_total: number;
  instancias_activas: number;
  reservas_activas: number;
  notas_registradas: number;
};

export type ReservaColoquio = {
  id: string;
  evaluacion_id: string;
  turno_id: string;
  alumno_id: string;
  fecha_hora: string;
  estado: string;
};

export type ResultadoColoquio = {
  id: string;
  evaluacion_id: string;
  alumno_id: string;
  nota_final: string;
};
