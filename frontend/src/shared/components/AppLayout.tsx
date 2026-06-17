import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "@/features/auth/hooks/AuthProvider";
import { usePermissions } from "@/features/auth/hooks/usePermissions";

const NAV_ITEMS = [
  { to: "/", label: "Inicio", permission: null },
  { to: "/comision", label: "Mi comisión", permission: "atrasados:ver" },
  { to: "/coordinacion", label: "Coordinación", permission: "equipos:asignar" },
  {
    to: "/admin",
    label: "Admin",
    permission: null,
    anyPermission: ["estructura:gestionar", "usuarios:gestionar"],
  },
  { to: "/finanzas", label: "Finanzas", permission: "liquidaciones:grilla" },
  { to: "/auditoria", label: "Auditoría", permission: "auditoria:ver" },
] as const;

export function AppLayout() {
  const { logout } = useAuth();
  const { hasPermission } = usePermissions();

  const visibleNav = NAV_ITEMS.filter((item) => {
    if ("anyPermission" in item && item.anyPermission) {
      return item.anyPermission.some((p) => hasPermission(p));
    }
    return item.permission === null || hasPermission(item.permission);
  });

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-6">
            <span className="font-semibold text-slate-900">activia-trace</span>
            <nav className="flex gap-4 text-sm">
              {visibleNav.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    isActive ? "font-medium text-slate-900" : "text-slate-600 hover:text-slate-900"
                  }
                  end={item.to === "/"}
                >
                  {item.label}
                </NavLink>
              ))}
            </nav>
          </div>
          <button
            type="button"
            onClick={() => void logout()}
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-100"
          >
            Salir
          </button>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}
