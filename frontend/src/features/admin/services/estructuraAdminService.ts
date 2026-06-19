import { api } from "@/shared/services/api";
import type { CarreraItem, CohorteItem, MateriaItem } from "@/features/admin/types/admin";

export async function fetchCarreras(): Promise<CarreraItem[]> {
  const { data } = await api.get<{ items: CarreraItem[] }>("/api/admin/carreras");
  return data.items;
}

export async function crearCarrera(payload: {
  codigo: string;
  nombre: string;
}): Promise<CarreraItem> {
  const { data } = await api.post<CarreraItem>("/api/admin/carreras", payload);
  return data;
}

export async function fetchMaterias(): Promise<MateriaItem[]> {
  const { data } = await api.get<{ items: MateriaItem[] }>("/api/admin/materias");
  return data.items;
}

export async function crearMateria(payload: {
  codigo: string;
  nombre: string;
}): Promise<MateriaItem> {
  const { data } = await api.post<MateriaItem>("/api/admin/materias", payload);
  return data;
}

export async function fetchCohortes(carreraId?: string): Promise<CohorteItem[]> {
  const params = carreraId ? { carrera_id: carreraId } : undefined;
  const { data } = await api.get<{ items: CohorteItem[] }>("/api/admin/cohortes", { params });
  return data.items;
}

export async function crearCohorte(payload: {
  carrera_id: string;
  nombre: string;
  anio: number;
  vig_desde: string;
}): Promise<CohorteItem> {
  const { data } = await api.post<CohorteItem>("/api/admin/cohortes", payload);
  return data;
}
