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

export type UsuarioAdminItem = {
  id: string;
  nombre: string | null;
  apellidos: string | null;
  legajo: string | null;
  facturador: boolean;
  estado: string;
};
