import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import {
  cerrarLiquidacion,
  fetchLiquidacionKpis,
  fetchLiquidaciones,
} from "@/features/finanzas/services/liquidacionService";
import type { LiquidacionSegmento } from "@/features/finanzas/types/finanzas";

const SEGMENTOS: { id: LiquidacionSegmento; label: string }[] = [
  { id: "general", label: "General" },
  { id: "nexo", label: "NEXO" },
  { id: "factura", label: "Factura" },
];

export function LiquidacionesPanel() {
  const [periodo, setPeriodo] = useState("2026-06");
  const [segmento, setSegmento] = useState<LiquidacionSegmento>("general");
  const queryClient = useQueryClient();

  const kpis = useQuery({
    queryKey: ["liq-kpis", periodo],
    queryFn: () => fetchLiquidacionKpis(periodo),
    retry: false,
  });

  const listado = useQuery({
    queryKey: ["liq-list", periodo, segmento],
    queryFn: () => fetchLiquidaciones(periodo, segmento),
    retry: false,
  });

  const cerrarMutation = useMutation({
    mutationFn: cerrarLiquidacion,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["liq-list"] });
      void queryClient.invalidateQueries({ queryKey: ["liq-kpis"] });
    },
  });

  const backendListo = !listado.isError;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end gap-3">
        <label className="text-sm">
          <span className="font-medium text-slate-700">Período</span>
          <input
            aria-label="Período liquidación"
            className="ml-2 rounded-lg border border-slate-300 px-3 py-2 text-sm"
            value={periodo}
            onChange={(e) => setPeriodo(e.target.value)}
          />
        </label>
        <div className="flex gap-1">
          {SEGMENTOS.map((s) => (
            <button
              key={s.id}
              type="button"
              className={
                segmento === s.id
                  ? "rounded-lg bg-slate-900 px-3 py-1.5 text-sm text-white"
                  : "rounded-lg px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-100"
              }
              onClick={() => setSegmento(s.id)}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {!backendListo && (
        <p className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          Módulo de liquidaciones pendiente (C-18 backend). La UI está lista para conectar
          `/api/liquidaciones/*`.
        </p>
      )}

      {kpis.data && (
        <div className="grid gap-3 sm:grid-cols-3">
          <Kpi label="Total general" value={kpis.data.total_general} />
          <Kpi label="Total NEXO" value={kpis.data.total_nexo} />
          <Kpi label="Total factura" value={kpis.data.total_factura} />
        </div>
      )}

      {listado.isLoading ? (
        <p className="text-sm text-slate-600">Cargando liquidaciones…</p>
      ) : (
        <ul className="divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white text-sm">
          {(listado.data ?? []).map((l) => (
            <li key={l.id} className="flex items-center justify-between px-4 py-2">
              <span>
                Docente {l.usuario_id.slice(0, 8)}… — ${l.total}
              </span>
              <div className="flex items-center gap-2">
                <span className="text-slate-500">{l.estado}</span>
                {l.estado === "Abierta" && (
                  <button
                    type="button"
                    className="text-xs text-slate-700 underline"
                    onClick={() => cerrarMutation.mutate(l.id)}
                  >
                    Cerrar
                  </button>
                )}
              </div>
            </li>
          ))}
          {backendListo && (listado.data ?? []).length === 0 && (
            <li className="px-4 py-4 text-center text-slate-500">
              Sin liquidaciones en este segmento.
            </li>
          )}
        </ul>
      )}
    </div>
  );
}

function Kpi({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-4 py-3">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="text-lg font-semibold text-slate-900">{value}</p>
    </div>
  );
}
