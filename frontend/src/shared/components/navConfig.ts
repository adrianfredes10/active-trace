export type NavItem = {
  to: string;
  label: string;
  permission: string | null;
  anyPermission?: readonly string[];
};

export type NavGroup = {
  id: string;
  label: string | null;
  items: readonly NavItem[];
};

export const NAV_GROUPS: readonly NavGroup[] = [
  {
    id: "home",
    label: null,
    items: [{ to: "/", label: "Inicio", permission: null }],
  },
  {
    id: "academico",
    label: "Académico",
    items: [
      { to: "/comision", label: "Mi comisión", permission: "atrasados:ver" },
      { to: "/encuentros", label: "Encuentros", permission: "encuentros:gestionar" },
      { to: "/coloquios", label: "Coloquios", permission: "evaluaciones:gestionar" },
    ],
  },
  {
    id: "coordinacion",
    label: "Coordinación",
    items: [{ to: "/coordinacion", label: "Coordinación", permission: "equipos:asignar" }],
  },
  {
    id: "finanzas",
    label: "Finanzas",
    items: [
      { to: "/finanzas", label: "Liquidaciones", permission: "liquidaciones:grilla" },
      { to: "/finanzas/facturas", label: "Facturas", permission: "facturas:gestionar" },
    ],
  },
  {
    id: "admin",
    label: "Administración",
    items: [
      {
        to: "/admin",
        label: "Panel",
        permission: null,
        anyPermission: ["estructura:gestionar", "usuarios:gestionar"],
      },
      { to: "/admin/carreras", label: "Carreras", permission: "estructura:gestionar" },
      { to: "/admin/materias", label: "Materias", permission: "estructura:gestionar" },
      { to: "/admin/cohortes", label: "Cohortes", permission: "estructura:gestionar" },
      { to: "/admin/usuarios", label: "Usuarios", permission: "usuarios:gestionar" },
    ],
  },
  {
    id: "auditoria",
    label: "Auditoría",
    items: [{ to: "/auditoria", label: "Auditoría", permission: "auditoria:ver" }],
  },
] as const;

export const ROUTE_TITLES: Record<string, string> = {
  "/": "Inicio",
  "/comision": "Mi comisión",
  "/encuentros": "Encuentros",
  "/encuentros/crear": "Crear encuentro",
  "/encuentros/guardias": "Guardias",
  "/coloquios": "Coloquios",
  "/coloquios/crear": "Nueva convocatoria",
  "/coordinacion": "Coordinación",
  "/admin": "Administración",
  "/admin/carreras": "Carreras",
  "/admin/materias": "Materias",
  "/admin/cohortes": "Cohortes",
  "/admin/usuarios": "Usuarios",
  "/finanzas": "Finanzas",
  "/finanzas/grilla": "Grilla salarial",
  "/finanzas/facturas": "Facturas",
  "/auditoria": "Auditoría",
};

export function isNavItemVisible(
  item: NavItem,
  hasPermission: (permission: string) => boolean,
): boolean {
  if (item.anyPermission?.length) {
    return item.anyPermission.some((p) => hasPermission(p));
  }
  return item.permission === null || hasPermission(item.permission);
}

export function filterVisibleGroups(
  groups: readonly NavGroup[],
  hasPermission: (permission: string) => boolean,
): NavGroup[] {
  return groups
    .map((group) => ({
      ...group,
      items: group.items.filter((item) => isNavItemVisible(item, hasPermission)),
    }))
    .filter((group) => group.items.length > 0);
}
