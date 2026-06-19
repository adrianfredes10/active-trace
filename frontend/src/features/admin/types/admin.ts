export type CarreraItem = {
  id: string;
  codigo: string;
  nombre: string;
  estado: string;
};

export type MateriaItem = {
  id: string;
  codigo: string;
  nombre: string;
  estado: string;
};

export type CohorteItem = {
  id: string;
  carrera_id: string;
  nombre: string;
  anio: number;
  estado: string;
};

export type UsuarioAdminItem = {
  id: string;
  nombre: string | null;
  apellidos: string | null;
  banco: string | null;
  regional: string | null;
  legajo: string | null;
  legajo_profesional: string | null;
  facturador: boolean;
  estado: string;
};
