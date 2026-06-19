import { Outlet } from "react-router-dom";

export function ColoquiosPage() {
  return (
    <div className="space-y-2">
      <div>
        <h1 className="font-display text-2xl font-semibold uppercase tracking-wide text-text-primary">
          Coloquios
        </h1>
        <p className="mt-1 text-sm text-text-secondary">
          Convocatorias, turnos y resultados de evaluaciones.
        </p>
      </div>
      <Outlet />
    </div>
  );
}
