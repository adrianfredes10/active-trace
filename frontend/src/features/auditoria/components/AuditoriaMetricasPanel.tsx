import { useQuery } from "@tanstack/react-query";
import type { ReactNode } from "react";

import {
  fetchAccionesPorDia,
  fetchComunicacionesPorDocente,
  fetchInteracciones,
} from "@/features/auditoria/services/auditoriaPanelService";

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

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <MetricBlock title="Acciones por día" loading={acciones.isLoading}>
        <ul className="space-y-1 text-sm">
          {(acciones.data ?? []).slice(0, 8).map((r, i) => (
            <li key={`${r.dia}-${r.accion}-${i}`} className="flex justify-between">
              <span className="text-slate-600">
                {r.dia} · {r.accion}
              </span>
              <span>{r.total}</span>
            </li>
          ))}
        </ul>
      </MetricBlock>

      <MetricBlock title="Comunicaciones por docente" loading={comunicaciones.isLoading}>
        <ul className="space-y-1 text-sm">
          {(comunicaciones.data ?? []).map((r, i) => (
            <li key={`${r.enviado_por}-${r.estado}-${i}`} className="flex justify-between">
              <span className="font-mono text-xs text-slate-500">
                {r.enviado_por.slice(0, 8)}…
              </span>
              <span>
                {r.estado} ({r.total})
              </span>
            </li>
          ))}
        </ul>
      </MetricBlock>

      <MetricBlock title="Interacciones agrupadas" loading={interacciones.isLoading} wide>
        <ul className="space-y-1 text-sm">
          {(interacciones.data ?? []).slice(0, 10).map((r, i) => (
            <li key={`${r.actor_id}-${r.accion}-${i}`} className="flex justify-between gap-2">
              <span className="truncate font-mono text-xs text-slate-500">{r.actor_id}</span>
              <span className="shrink-0">{r.accion}</span>
              <span className="shrink-0">{r.total}</span>
            </li>
          ))}
        </ul>
      </MetricBlock>
    </div>
  );
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
      <h3 className="mb-2 text-sm font-medium text-slate-800">{title}</h3>
      <div className="rounded-lg border border-slate-200 bg-white p-4">
        {loading ? <p className="text-sm text-slate-600">Cargando…</p> : children}
      </div>
    </div>
  );
}
