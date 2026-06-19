import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { useAuth } from "@/features/auth/hooks/AuthProvider";
import { usePermissions } from "@/features/auth/hooks/usePermissions";
import { fetchResumenAcademico } from "@/features/admin/services/adminDashboardService";
import { KpiCard } from "@/shared/components/charts/KpiCard";
import { isNavPathAllowedForPersona } from "@/shared/lib/navPersona";

const MODULE_LINKS = [
  { to: "/admin", label: "Panel admin" },
  { to: "/comision", label: "Mi comisión" },
  { to: "/encuentros", label: "Crear encuentro" },
  { to: "/coloquios", label: "Coloquios" },
  { to: "/coordinacion", label: "Coordinación" },
  { to: "/finanzas", label: "Finanzas" },
  { to: "/auditoria", label: "Auditoría" },
] as const;

export function HomePage() {
  const { user } = useAuth();
  const { hasPermission, persona } = usePermissions();
  const canSeeResumen = persona === "ADMIN" && hasPermission("estructura:gestionar");

  const resumen = useQuery({
    queryKey: ["admin-resumen"],
    queryFn: fetchResumenAcademico,
    enabled: canSeeResumen,
    retry: 1,
  });

  const visibleModules = MODULE_LINKS.filter((m) => {
    if (!isNavPathAllowedForPersona(m.to, persona)) return false;
    if (m.to === "/admin") {
      return hasPermission("estructura:gestionar") || hasPermission("usuarios:gestionar");
    }
    if (m.to === "/comision") return hasPermission("atrasados:ver");
    if (m.to === "/encuentros") return hasPermission("encuentros:gestionar");
    if (m.to === "/coloquios") return hasPermission("evaluaciones:gestionar");
    if (m.to === "/coordinacion") return hasPermission("equipos:asignar");
    if (m.to === "/finanzas") {
      return hasPermission("liquidaciones:grilla") || hasPermission("facturas:gestionar");
    }
    if (m.to === "/auditoria") return hasPermission("auditoria:ver");
    return true;
  });

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
