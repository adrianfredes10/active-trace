import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { PageHeader } from "@/features/admin/components/shared/PageHeader";
import {
  fetchConvocatorias,
  fetchMetricasGlobales,
} from "@/features/coloquios/services/coloquioService";
import { KpiCard } from "@/shared/components/charts/KpiCard";

export function ColoquiosDashboardPage() {
  const metricas = useQuery({
    queryKey: ["coloquios-metricas"],
    queryFn: fetchMetricasGlobales,
    retry: 1,
  });
  const convocatorias = useQuery({
    queryKey: ["coloquios-convocatorias"],
    queryFn: fetchConvocatorias,
    retry: 1,
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <PageHeader title="Coloquios" subtitle="Convocatorias, reservas y resultados." />
        <Link
          to="/coloquios/crear"
          className="inline-flex h-10 items-center rounded-md bg-ink-900 px-4 text-sm font-medium text-white no-underline hover:bg-ink-700"
        >
          Nueva convocatoria
        </Link>
      </div>

      {metricas.data && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <KpiCard label="Convocados" value={metricas.data.convocados_total} />
          <KpiCard label="Activas" value={metricas.data.instancias_activas} />
          <KpiCard label="Reservas" value={metricas.data.reservas_activas} />
          <KpiCard label="Notas" value={metricas.data.notas_registradas} />
        </div>
      )}

      {convocatorias.isLoading && <p className="text-sm text-text-secondary">Cargando…</p>}
      {convocatorias.isError && (
        <p className="text-sm text-status-danger">No se pudieron cargar las convocatorias.</p>
      )}

      {!convocatorias.isLoading && !convocatorias.isError && (
        <div className="overflow-x-auto rounded-lg border border-border bg-surface-card">
          <table className="min-w-full text-sm">
            <thead className="border-b border-border bg-surface text-left text-xs uppercase text-text-secondary">
              <tr>
                <th className="px-4 py-2">Instancia</th>
                <th className="px-4 py-2">Estado</th>
                <th className="px-4 py-2">Convocados</th>
                <th className="px-4 py-2">Reservas</th>
                <th className="px-4 py-2">Cupos</th>
                <th className="px-4 py-2" />
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {(convocatorias.data ?? []).map((c) => (
                <tr key={c.evaluacion_id} className="hover:bg-surface/60">
                  <td className="px-4 py-2 font-medium">{c.instancia}</td>
                  <td className="px-4 py-2">{c.estado}</td>
                  <td className="px-4 py-2 tabular-nums">{c.convocados}</td>
                  <td className="px-4 py-2 tabular-nums">{c.reservas_activas}</td>
                  <td className="px-4 py-2 tabular-nums">{c.cupos_libres}</td>
                  <td className="px-4 py-2 text-right">
                    <Link
                      to={`/coloquios/${c.evaluacion_id}`}
                      className="font-medium text-ink-700 underline"
                    >
                      Ver
                    </Link>
                  </td>
                </tr>
              ))}
              {(convocatorias.data ?? []).length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-text-secondary">
                    Sin convocatorias.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
