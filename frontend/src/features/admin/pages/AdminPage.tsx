import { useState } from "react";

import { EstructuraPanel } from "@/features/admin/components/EstructuraPanel";
import { ProfesorAltaPanel } from "@/features/admin/components/ProfesorAltaPanel";
import { UsuariosPanel } from "@/features/admin/components/UsuariosPanel";
import { usePermissions } from "@/features/auth/hooks/usePermissions";

const TABS = [
  { id: "estructura", label: "Estructura", permission: "estructura:gestionar" },
  { id: "usuarios", label: "Usuarios", permission: "usuarios:gestionar" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export function AdminPage() {
  const { hasPermission, isLoading } = usePermissions();
  const visibleTabs = TABS.filter((t) => hasPermission(t.permission));
  const [tab, setTab] = useState<TabId>("estructura");

  const activeTab = visibleTabs.some((t) => t.id === tab)
    ? tab
    : (visibleTabs[0]?.id ?? "estructura");

  if (isLoading) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold text-slate-900">Administración</h1>
        <p className="text-sm text-slate-600">Cargando permisos…</p>
      </div>
    );
  }

  if (visibleTabs.length === 0) {
    return (
      <div className="space-y-4 rounded-lg border border-amber-200 bg-amber-50 p-4">
        <h1 className="text-2xl font-semibold text-slate-900">Administración</h1>
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
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Administración</h1>
        <p className="mt-1 text-sm text-slate-600">
          Alta de carreras, materias y usuarios del tenant.
        </p>
      </div>

      <div className="flex flex-wrap gap-2 border-b border-slate-200 pb-2">
        {visibleTabs.map((t) => (
          <button
            key={t.id}
            type="button"
            className={
              activeTab === t.id
                ? "rounded-lg bg-slate-900 px-3 py-1.5 text-sm text-white"
                : "rounded-lg px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-100"
            }
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {activeTab === "estructura" && <EstructuraPanel />}
      {activeTab === "usuarios" && (
        <div className="space-y-8">
          <ProfesorAltaPanel />
          <UsuariosPanel />
        </div>
      )}
    </div>
  );
}
