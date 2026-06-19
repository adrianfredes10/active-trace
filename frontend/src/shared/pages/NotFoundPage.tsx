import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-surface px-4 text-center">
      <p className="font-display text-6xl font-semibold text-ink-900">404</p>
      <h1 className="mt-2 text-lg font-semibold text-text-primary">Página no encontrada</h1>
      <p className="mt-1 max-w-sm text-sm text-text-secondary">
        La ruta que buscás no existe o no tenés permiso para verla.
      </p>
      <Link
        to="/"
        className="mt-6 inline-flex h-10 items-center justify-center rounded-md bg-ink-900 px-4 text-sm font-medium text-white no-underline hover:bg-ink-700"
      >
        Volver al inicio
      </Link>
    </div>
  );
}
