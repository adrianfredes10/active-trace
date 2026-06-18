import type { AsignacionItem } from "@/features/comision/types/comision";

export type ComisionWorkspace = {
  key: string;
  asignacion: AsignacionItem;
  comision: string | null;
};

export function buildComisionWorkspaces(equipos: AsignacionItem[]): ComisionWorkspace[] {
  const workspaces: ComisionWorkspace[] = [];
  for (const asignacion of equipos) {
    const comisiones = asignacion.comisiones?.length ? asignacion.comisiones : [null];
    for (const comision of comisiones) {
      workspaces.push({
        key: `${asignacion.id}::${comision ?? "*"}`,
        asignacion,
        comision,
      });
    }
  }
  return workspaces;
}

export function workspaceLabel(workspace: ComisionWorkspace): string {
  const materia = workspace.asignacion.materia_codigo ?? workspace.asignacion.materia_nombre ?? "Materia";
  const cohorte = workspace.asignacion.cohorte_nombre ?? "cohorte";
  const carrera = workspace.asignacion.carrera_codigo
    ? `${workspace.asignacion.carrera_codigo} · `
    : "";
  const comision = workspace.comision ? ` — Comisión ${workspace.comision}` : "";
  return `${carrera}${materia} / ${cohorte}${comision}`;
}
