import { useQuery } from "@tanstack/react-query";
import type { ReactNode } from "react";

import {
  fetchAccionesPorDia,
  fetchComunicacionesPorDocente,
  fetchInteracciones,
} from "@/features/auditoria/services/auditoriaPanelService";
import { SimpleBarChart } from "@/shared/components/charts/SimpleBarChart";

export function AuditoriaMetricasPanel() {
  const acciones = useQuery({
    queryKey: ["aud-acciones-dia"],
    queryFn: () => fetchAccionesPorDia(),
  });
  const comunicaciones = useQuery({
    queryKey: ["aud-com-docente"],
    queryFn: fetchComunicacionesPorDocente,
  });
  const interacciones = useQuery({
    queryKey: ["aud-interacciones"],
    queryFn: () => fetchInteracciones(),
  });

  const accionesPorDia = aggregateByDay(acciones.data ?? []);

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <MetricBlock title="Acciones por día" loading={acciones.isLoading}>
        <SimpleBarChart
          items={accionesPorDia.map((row) => ({ label: row.dia, value: row.total }))}
          emptyLabel="Sin acciones registradas."
        />
        <ul className="mt-4 max-h-40 space-y-1 overflow-y-auto border-t border-border pt-3 text-xs text-text-secondary">
          {(acciones.data ?? []).slice(0, 6).map((r, i) => (
            <li key={`${r.dia}-${r.accion}-${i}`} className="flex justify-between gap-2">
              <span className="truncate">
                {r.dia} · {r.accion}
              </span>
              <span className="shrink-0 tabular-nums">{r.total}</span>
            </li>
          ))}
        </ul>
      </MetricBlock>

      <MetricBlock title="Comunicaciones por docente" loading={comunicaciones.isLoading}>
        <SimpleBarChart
          items={(comunicaciones.data ?? []).slice(0, 8).map((r, i) => ({
            label: `${r.enviado_por.slice(0, 8)}… · ${r.estado}`,
            value: r.total,
            colorClass: i % 2 === 0 ? "bg-ink-700" : "bg-accent-gold",
          }))}
          emptyLabel="Sin comunicaciones."
        />
      </MetricBlock>

      <MetricBlock title="Interacciones agrupadas" loading={interacciones.isLoading} wide>
        <SimpleBarChart
          items={(interacciones.data ?? []).slice(0, 10).map((r) => ({
            label: `${r.accion} (${r.actor_id.slice(0, 8)}…)`,
            value: r.total,
            colorClass: "bg-slate-500",
          }))}
          emptyLabel="Sin interacciones."
        />
      </MetricBlock>
    </div>
  );
}

function aggregateByDay(rows: { dia: string; accion: string; total: number }[]) {
  const map = new Map<string, number>();
  for (const row of rows) {
    map.set(row.dia, (map.get(row.dia) ?? 0) + row.total);
  }
  return [...map.entries()]
    .map(([dia, total]) => ({ dia, total }))
    .sort((a, b) => a.dia.localeCompare(b.dia))
    .slice(-10);
}

function MetricBlock({
  title,
  loading,
  wide,
  children,
}: {
  title: string;
  loading: boolean;
  wide?: boolean;
  children: ReactNode;
}) {
  return (
    <div className={wide ? "lg:col-span-2" : ""}>
      <h3 className="mb-2 text-sm font-medium text-text-primary">{title}</h3>
      <div className="rounded-lg border border-border bg-surface-card p-4 shadow-sm">
        {loading ? <p className="text-sm text-text-secondary">Cargando…</p> : children}
      </div>
    </div>
  );
}
