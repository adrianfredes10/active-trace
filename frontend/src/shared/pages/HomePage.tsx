import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { useAuth } from "@/features/auth/hooks/AuthProvider";
import { usePermissions } from "@/features/auth/hooks/usePermissions";
import { fetchResumenAcademico } from "@/features/admin/services/adminDashboardService";
import { KpiCard } from "@/shared/components/charts/KpiCard";

export function HomePage() {
  const { user } = useAuth();
  const { hasPermission } = usePermissions();
  const canSeeResumen = hasPermission("estructura:gestionar");

  const resumen = useQuery({
    queryKey: ["admin-resumen"],
    queryFn: fetchResumenAcademico,
    enabled: canSeeResumen,
    retry: 1,
  });

  const visibleModules = [
    { to: "/admin", label: "Panel admin", show: canSeeResumen || hasPermission("usuarios:gestionar") },
    { to: "/comision", label: "Mi comisión", show: hasPermission("atrasados:ver") },
    { to: "/encuentros", label: "Encuentros", show: hasPermission("encuentros:gestionar") },
    { to: "/coloquios", label: "Coloquios", show: hasPermission("evaluaciones:gestionar") },
    { to: "/coordinacion", label: "Coordinación", show: hasPermission("equipos:asignar") },
    {
      to: "/finanzas",
      label: "Finanzas",
      show: hasPermission("liquidaciones:grilla") || hasPermission("facturas:gestionar"),
    },
    { to: "/auditoria", label: "Auditoría", show: hasPermission("auditoria:ver") },
  ].filter((m) => m.show);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Panel principal</h1>
        <p className="mt-1 text-sm text-slate-600">
          Hola{user?.email ? `, ${user.email}` : ""}. Instituto Demo — tenant{" "}
          <strong>demo</strong>.
        </p>
      </div>

      {canSeeResumen && resumen.data && (
        <section className="space-y-3">
          <h2 className="text-lg font-medium text-text-primary">Resumen académico</h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <KpiCard label="Alumnos" value={resumen.data.total_alumnos} />
            <KpiCard label="Entregas" value={resumen.data.total_calificaciones} />
            <KpiCard label="Aprobadas" value={resumen.data.entregas_aprobadas} />
            <KpiCard label="Pendientes" value={resumen.data.entregas_pendientes} />
          </div>
        </section>
      )}

      {visibleModules.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-lg font-medium text-text-primary">Tus módulos</h2>
          <div className="flex flex-wrap gap-2">
            {visibleModules.map((m) => (
              <Link
                key={m.to}
                to={m.to}
                className="inline-flex items-center rounded-md border border-border bg-surface-card px-4 py-2 text-sm font-medium text-text-primary no-underline hover:bg-surface"
              >
                {m.label} →
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
