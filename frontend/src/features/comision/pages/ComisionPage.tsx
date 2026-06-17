import { useState } from "react";

import { PermissionGate } from "@/features/auth/components/PermissionGate";
import { AtrasadosTable } from "@/features/comision/components/AtrasadosTable";
import { CalificacionesImportPanel } from "@/features/comision/components/CalificacionesImportPanel";
import { ComisionContextBar } from "@/features/comision/components/ComisionContextBar";
import { ComunicacionAtrasadosPanel } from "@/features/comision/components/ComunicacionAtrasadosPanel";
import { ReportesPanel } from "@/features/comision/components/ReportesPanel";
import { UmbralPanel } from "@/features/comision/components/UmbralPanel";
import { ComisionProvider } from "@/features/comision/hooks/ComisionProvider";

const TABS = [
  { id: "atrasados", label: "Atrasados", permission: "atrasados:ver" },
  { id: "importar", label: "Importar", permission: "calificaciones:importar" },
  { id: "umbral", label: "Umbral", permission: "calificaciones:importar" },
  { id: "reportes", label: "Reportes", permission: "atrasados:ver" },
  { id: "comunicar", label: "Comunicar", permission: "comunicacion:enviar" },
] as const;

type TabId = (typeof TABS)[number]["id"];

function ComisionContent() {
  const [tab, setTab] = useState<TabId>("atrasados");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Mi comisión</h1>
        <p className="mt-1 text-sm text-slate-600">
          Importación, análisis de atrasados y comunicaciones a alumnos.
        </p>
      </div>

      <ComisionContextBar />

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

      {tab === "atrasados" && (
        <PermissionGate permission="atrasados:ver">
          <AtrasadosTable />
        </PermissionGate>
      )}
      {tab === "importar" && (
        <PermissionGate permission="calificaciones:importar">
          <CalificacionesImportPanel />
        </PermissionGate>
      )}
      {tab === "umbral" && (
        <PermissionGate permission="calificaciones:importar">
          <UmbralPanel />
        </PermissionGate>
      )}
      {tab === "reportes" && (
        <PermissionGate permission="atrasados:ver">
          <ReportesPanel />
        </PermissionGate>
      )}
      {tab === "comunicar" && (
        <PermissionGate permission="comunicacion:enviar">
          <ComunicacionAtrasadosPanel />
        </PermissionGate>
      )}
    </div>
  );
}

export function ComisionPage() {
  return (
    <ComisionProvider>
      <ComisionContent />
    </ComisionProvider>
  );
}
