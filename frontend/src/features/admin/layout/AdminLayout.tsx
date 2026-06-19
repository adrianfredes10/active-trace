import { NavLink, Outlet } from "react-router-dom";

import { usePermissions } from "@/features/auth/hooks/usePermissions";

const ADMIN_TABS = [
  { to: "/admin", label: "Panel", end: true, permission: null as string | null, anyOf: ["estructura:gestionar", "usuarios:gestionar"] },
  { to: "/admin/carreras", label: "Carreras", end: false, permission: "estructura:gestionar", anyOf: [] as string[] },
  { to: "/admin/materias", label: "Materias", end: false, permission: "estructura:gestionar", anyOf: [] as string[] },
  { to: "/admin/cohortes", label: "Cohortes", end: false, permission: "estructura:gestionar", anyOf: [] as string[] },
  { to: "/admin/usuarios", label: "Usuarios", end: false, permission: "usuarios:gestionar", anyOf: [] as string[] },
] as const;

export function AdminLayout() {
  const { hasPermission, isLoading } = usePermissions();

  const visibleTabs = ADMIN_TABS.filter((tab) => {
    if (tab.anyOf.length > 0) {
      return tab.anyOf.some((p) => hasPermission(p));
    }
    return tab.permission === null || hasPermission(tab.permission);
  });

  if (isLoading) {
    return <p className="text-sm text-text-secondary">Cargando permisos…</p>;
  }

  if (visibleTabs.length === 0) {
    return (
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
        <p className="text-sm text-amber-900">
          Tu usuario no tiene permisos de administración. Iniciá sesión como{" "}
          <strong>admin@demo.local</strong> / <strong>Admin1234!</strong> (tenant{" "}
          <strong>demo</strong>).
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <nav
        className="-mx-1 flex gap-1 overflow-x-auto border-b border-border pb-2 scrollbar-thin"
        aria-label="Secciones de administración"
      >
        {visibleTabs.map((tab) => (
          <NavLink
            key={tab.to}
            to={tab.to}
            end={tab.end}
            className={({ isActive }) =>
              `focus-ring shrink-0 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? "bg-ink-900 text-white"
                  : "text-text-secondary hover:bg-surface-card hover:text-text-primary"
              }`
            }
          >
            {tab.label}
          </NavLink>
        ))}
      </nav>

      <Outlet />
    </div>
  );
}
