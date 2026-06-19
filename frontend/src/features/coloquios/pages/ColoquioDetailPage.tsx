import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { PageHeader } from "@/features/admin/components/shared/PageHeader";
import {
  cerrarConvocatoria,
  fetchAgendaColoquios,
  fetchConvocatoriaDetalle,
  fetchResultadosColoquios,
} from "@/features/coloquios/services/coloquioService";
import { KpiCard } from "@/shared/components/charts/KpiCard";
import { Button } from "@/shared/components/ui/Button";
import { showToast } from "@/shared/components/ui/Toast";

export function ColoquioDetailPage() {
  const { evaluacionId = "" } = useParams();
  const queryClient = useQueryClient();

  const detalle = useQuery({
    queryKey: ["coloquio-detalle", evaluacionId],
    queryFn: () => fetchConvocatoriaDetalle(evaluacionId),
    enabled: Boolean(evaluacionId),
  });
  const agenda = useQuery({
    queryKey: ["coloquios-agenda"],
    queryFn: fetchAgendaColoquios,
  });
  const resultados = useQuery({
    queryKey: ["coloquios-resultados"],
    queryFn: fetchResultadosColoquios,
  });

  const cerrar = useMutation({
    mutationFn: () => cerrarConvocatoria(evaluacionId),
    onSuccess: () => {
      showToast("Convocatoria cerrada.");
      void queryClient.invalidateQueries({ queryKey: ["coloquio-detalle", evaluacionId] });
      void queryClient.invalidateQueries({ queryKey: ["coloquios-convocatorias"] });
    },
  });

  const reservasConvocatoria = (agenda.data ?? []).filter((r) => r.evaluacion_id === evaluacionId);
  const resultadosConvocatoria = (resultados.data ?? []).filter(
    (r) => r.evaluacion_id === evaluacionId,
  );

  if (detalle.isLoading) {
    return <p className="text-sm text-text-secondary">Cargando convocatoria…</p>;
  }

  if (detalle.isError || !detalle.data) {
    return (
      <p className="text-sm text-status-danger">
        No se encontró la convocatoria.{" "}
        <Link to="/coloquios" className="underline">
          Volver al panel
        </Link>
      </p>
    );
  }

  const c = detalle.data;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <PageHeader title={c.instancia} subtitle={`Estado: ${c.estado} · Tipo: ${c.tipo}`} />
        {c.estado !== "cerrada" && (
          <Button
            type="button"
            variant="secondary"
            disabled={cerrar.isPending}
            onClick={() => cerrar.mutate()}
          >
            Cerrar convocatoria
          </Button>
        )}
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard label="Convocados" value={c.convocados} />
        <KpiCard label="Reservas activas" value={c.reservas_activas} />
        <KpiCard label="Cupos libres" value={c.cupos_libres} />
        <KpiCard label="Notas registradas" value={c.notas_registradas} />
      </div>

      <section className="space-y-2">
        <h3 className="text-sm font-semibold text-text-primary">Reservas</h3>
        <div className="overflow-x-auto rounded-lg border border-border bg-surface-card">
          <table className="min-w-full text-sm">
            <thead className="border-b border-border bg-surface text-left text-xs uppercase text-text-secondary">
              <tr>
                <th className="px-4 py-2">Alumno</th>
                <th className="px-4 py-2">Fecha/hora</th>
                <th className="px-4 py-2">Estado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {reservasConvocatoria.map((r) => (
                <tr key={r.id}>
                  <td className="px-4 py-2 font-mono text-xs">{r.alumno_id.slice(0, 8)}…</td>
                  <td className="px-4 py-2">{new Date(r.fecha_hora).toLocaleString()}</td>
                  <td className="px-4 py-2">{r.estado}</td>
                </tr>
              ))}
              {reservasConvocatoria.length === 0 && (
                <tr>
                  <td colSpan={3} className="px-4 py-4 text-center text-text-secondary">
                    Sin reservas.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="space-y-2">
        <h3 className="text-sm font-semibold text-text-primary">Resultados</h3>
        <div className="overflow-x-auto rounded-lg border border-border bg-surface-card">
          <table className="min-w-full text-sm">
            <thead className="border-b border-border bg-surface text-left text-xs uppercase text-text-secondary">
              <tr>
                <th className="px-4 py-2">Alumno</th>
                <th className="px-4 py-2">Nota</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {resultadosConvocatoria.map((r) => (
                <tr key={r.id}>
                  <td className="px-4 py-2 font-mono text-xs">{r.alumno_id.slice(0, 8)}…</td>
                  <td className="px-4 py-2 font-medium">{r.nota_final}</td>
                </tr>
              ))}
              {resultadosConvocatoria.length === 0 && (
                <tr>
                  <td colSpan={2} className="px-4 py-4 text-center text-text-secondary">
                    Sin resultados cargados.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <Link to="/coloquios" className="text-sm font-medium text-ink-700 underline">
        ← Volver al panel
      </Link>
    </div>
  );
}
