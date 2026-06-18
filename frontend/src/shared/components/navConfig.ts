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
    items: [{ to: "/comision", label: "Mi comisión", permission: "atrasados:ver" }],
  },
  {
    id: "coordinacion",
    label: "Coordinación",
    items: [{ to: "/coordinacion", label: "Coordinación", permission: "equipos:asignar" }],
  },
  {
    id: "finanzas",
    label: "Finanzas",
    items: [{ to: "/finanzas", label: "Finanzas", permission: "liquidaciones:grilla" }],
  },
  {
    id: "admin",
    label: "Administración",
    items: [
      {
        to: "/admin",
        label: "Admin",
        permission: null,
        anyPermission: ["estructura:gestionar", "usuarios:gestionar"],
      },
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
  "/coordinacion": "Coordinación",
  "/admin": "Administración",
  "/finanzas": "Finanzas",
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
