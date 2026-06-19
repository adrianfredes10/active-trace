import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { fetchResumenAcademico } from "@/features/admin/services/adminDashboardService";
import { PageHeader } from "@/features/admin/components/shared/PageHeader";
import { KpiCard } from "@/shared/components/charts/KpiCard";
import { SimpleBarChart } from "@/shared/components/charts/SimpleBarChart";

export function AdminDashboardPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["admin-resumen"],
    queryFn: fetchResumenAcademico,
    retry: 1,
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Panel académico"
        subtitle="Resumen del tenant: alumnos, entregas y estructura."
      />

      {isLoading && <p className="text-sm text-text-secondary">Cargando métricas…</p>}
      {isError && (
        <p className="text-sm text-status-danger" role="alert">
          No se pudo cargar el resumen. Verificá que la API esté en marcha.
        </p>
      )}

      {data && (
        <>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <KpiCard label="Alumnos activos" value={data.total_alumnos} hint="Padrón en versiones activas" />
            <KpiCard label="Entregas totales" value={data.total_calificaciones} />
            <KpiCard
              label="Aprobadas"
              value={data.entregas_aprobadas}
              hint={`${data.entregas_pendientes} pendientes`}
            />
            <KpiCard
              label="Estructura"
              value={`${data.total_carreras} / ${data.total_materias}`}
              hint={`${data.total_cohortes} cohortes`}
            />
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <section className="rounded-lg border border-border bg-surface-card p-4 shadow-sm">
              <h3 className="mb-4 text-sm font-semibold text-text-primary">Alumnos por comisión</h3>
              <SimpleBarChart
                items={data.por_comision.map((row) => ({
                  label: `Comisión ${row.comision}`,
                  value: row.total,
                }))}
                emptyLabel="Sin alumnos en padrón activo."
              />
            </section>

            <section className="rounded-lg border border-border bg-surface-card p-4 shadow-sm">
              <h3 className="mb-4 text-sm font-semibold text-text-primary">Estado de entregas</h3>
              <SimpleBarChart
                items={[
                  { label: "Aprobadas", value: data.entregas_aprobadas, colorClass: "bg-emerald-500" },
                  { label: "Pendientes", value: data.entregas_pendientes, colorClass: "bg-amber-500" },
                ]}
              />
            </section>
          </div>

          <div className="flex flex-wrap gap-2">
            <Link
              to="/admin/carreras"
              className="inline-flex h-10 items-center justify-center rounded-md bg-ink-900 px-4 text-sm font-medium text-white no-underline hover:bg-ink-700"
            >
              Gestionar carreras
            </Link>
            <Link
              to="/admin/usuarios"
              className="inline-flex h-10 items-center justify-center rounded-md border border-border bg-surface-card px-4 text-sm font-medium text-text-primary no-underline hover:bg-surface"
            >
              Gestionar usuarios
            </Link>
          </div>
        </>
      )}
    </div>
  );
}
