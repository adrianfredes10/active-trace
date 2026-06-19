import { Outlet } from "react-router-dom";

export function FinanzasPage() {
  return (
    <div className="space-y-2">
      <div>
        <h1 className="font-display text-2xl font-semibold uppercase tracking-wide text-text-primary">
          Finanzas
        </h1>
        <p className="mt-1 text-sm text-text-secondary">
          Liquidaciones, grilla salarial y facturas.
        </p>
      </div>
      <Outlet />
    </div>
  );
}
