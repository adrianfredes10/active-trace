import { Outlet } from "react-router-dom";

export function EncuentrosPage() {
  return (
    <div className="space-y-2">
      <div>
        <h1 className="font-display text-2xl font-semibold uppercase tracking-wide text-text-primary">
          Encuentros
        </h1>
        <p className="mt-1 text-sm text-text-secondary">
          Clases, encuentros virtuales y guardias.
        </p>
      </div>
      <Outlet />
    </div>
  );
}
