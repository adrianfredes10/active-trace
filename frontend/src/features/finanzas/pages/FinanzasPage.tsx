import { useState } from "react";

import { PermissionGate } from "@/features/auth/components/PermissionGate";
import { GrillaSalarialPanel } from "@/features/finanzas/components/GrillaSalarialPanel";
import { LiquidacionesPanel } from "@/features/finanzas/components/LiquidacionesPanel";

const TABS = [
  { id: "liquidaciones", label: "Liquidaciones", permission: "liquidaciones:grilla" },
  { id: "grilla", label: "Grilla salarial", permission: "liquidaciones:grilla" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export function FinanzasPage() {
  const [tab, setTab] = useState<TabId>("liquidaciones");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Finanzas</h1>
        <p className="mt-1 text-sm text-slate-600">
          Liquidaciones de honorarios, grilla salarial y facturas.
        </p>
      </div>

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

      {tab === "liquidaciones" && (
        <PermissionGate permission="liquidaciones:grilla">
          <LiquidacionesPanel />
        </PermissionGate>
      )}
      {tab === "grilla" && (
        <PermissionGate permission="liquidaciones:grilla">
          <GrillaSalarialPanel />
        </PermissionGate>
      )}
    </div>
  );
}
