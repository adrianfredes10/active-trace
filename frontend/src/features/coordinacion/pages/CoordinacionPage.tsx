import { useState } from "react";

import { PermissionGate } from "@/features/auth/components/PermissionGate";
import { AvisosPanel } from "@/features/coordinacion/components/AvisosPanel";
import { CoordinacionContextBar } from "@/features/coordinacion/components/CoordinacionContextBar";
import { EquiposPanel } from "@/features/coordinacion/components/EquiposPanel";
import { MonitorGeneralPanel } from "@/features/coordinacion/components/MonitorGeneralPanel";
import { TareasPanel } from "@/features/coordinacion/components/TareasPanel";
import { CoordinacionProvider } from "@/features/coordinacion/hooks/CoordinacionProvider";

const TABS = [
  { id: "equipos", label: "Equipos", permission: "equipos:asignar" },
  { id: "avisos", label: "Avisos", permission: "avisos:publicar" },
  { id: "tareas", label: "Tareas", permission: "tareas:gestionar" },
  { id: "monitor", label: "Monitor", permission: "atrasados:ver" },
] as const;

type TabId = (typeof TABS)[number]["id"];

function CoordinacionContent() {
  const [tab, setTab] = useState<TabId>("equipos");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Coordinación</h1>
        <p className="mt-1 text-sm text-slate-600">
          Equipos docentes, avisos, tareas internas y monitores transversales.
        </p>
      </div>

      <CoordinacionContextBar />

      <div className="flex flex-wrap gap-2 border-b border-slate-200 pb-2">
        {TABS.map((t) => (
          <PermissionGate key={t.id} permission={t.permission}>
            <button
              type="button"
              className={
                tab === t.id
                  ? "rounded-lg bg-slate-900 px-3 py-1.5 text-sm text-white"
                  : "rounded-lg px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-100"
              }
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          </PermissionGate>
        ))}
      </div>

      {tab === "equipos" && (
        <PermissionGate permission="equipos:asignar">
          <EquiposPanel />
        </PermissionGate>
      )}
      {tab === "avisos" && (
        <PermissionGate permission="avisos:publicar">
          <AvisosPanel />
        </PermissionGate>
      )}
      {tab === "tareas" && (
        <PermissionGate permission="tareas:gestionar">
          <TareasPanel />
        </PermissionGate>
      )}
      {tab === "monitor" && (
        <PermissionGate permission="atrasados:ver">
          <MonitorGeneralPanel />
        </PermissionGate>
      )}
    </div>
  );
}

export function CoordinacionPage() {
  return (
    <CoordinacionProvider>
      <CoordinacionContent />
    </CoordinacionProvider>
  );
}
