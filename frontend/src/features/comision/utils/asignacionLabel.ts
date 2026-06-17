import type { AsignacionItem } from "@/features/comision/types/comision";

export function asignacionLabel(item: AsignacionItem): string {
  const materia = item.materia_codigo ?? item.materia_nombre ?? "Materia";
  const cohorte = item.cohorte_nombre ?? "cohorte";
  const carrera = item.carrera_codigo ? `${item.carrera_codigo} · ` : "";
  return `${carrera}${materia} — ${cohorte} (${item.rol})`;
}
