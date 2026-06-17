import { useState } from "react";

import { AuditoriaLogFilters } from "@/features/auditoria/components/AuditoriaLogFilters";
import { AuditoriaMetricasPanel } from "@/features/auditoria/components/AuditoriaMetricasPanel";

const TABS = [
  { id: "panel", label: "Panel" },
  { id: "log", label: "Log completo" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export function AuditoriaPage() {
  const [tab, setTab] = useState<TabId>("panel");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Auditoría</h1>
        <p className="mt-1 text-sm text-slate-600">
          Panel de métricas y log append-only con filtros.
        </p>
      </div>

      <div className="flex gap-2 border-b border-slate-200 pb-2">
        {TABS.map((t) => (
          <button
            key={t.id}
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
        ))}
      </div>

      {tab === "panel" && <AuditoriaMetricasPanel />}
      {tab === "log" && <AuditoriaLogFilters />}
    </div>
  );
}
