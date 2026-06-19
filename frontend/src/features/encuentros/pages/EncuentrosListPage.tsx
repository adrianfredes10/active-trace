import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { PageHeader } from "@/features/admin/components/shared/PageHeader";
import { fetchEncuentrosAdmin } from "@/features/encuentros/services/encuentroService";
import { StatusBadge } from "@/shared/components/StatusBadge";

export function EncuentrosListPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["encuentros-admin"],
    queryFn: fetchEncuentrosAdmin,
    retry: 1,
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <PageHeader title="Encuentros" subtitle="Instancias programadas del tenant." />
        <Link
          to="/encuentros/crear"
          className="inline-flex h-10 shrink-0 items-center rounded-md bg-ink-900 px-4 text-sm font-medium text-white no-underline hover:bg-ink-700"
        >
          Crear encuentro
        </Link>
      </div>

      {isLoading && <p className="text-sm text-text-secondary">Cargando…</p>}
      {isError && (
        <p className="text-sm text-status-danger" role="alert">
          No se pudo cargar el listado.
        </p>
      )}

      {!isLoading && !isError && (
        <div className="overflow-x-auto rounded-lg border border-border bg-surface-card">
          <table className="min-w-full text-sm">
            <thead className="border-b border-border bg-surface text-left text-xs uppercase tracking-wide text-text-secondary">
              <tr>
                <th className="px-4 py-2 font-medium">Fecha</th>
                <th className="px-4 py-2 font-medium">Hora</th>
                <th className="px-4 py-2 font-medium">Título</th>
                <th className="px-4 py-2 font-medium">Estado</th>
                <th className="px-4 py-2 font-medium">Meet</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {(data ?? []).map((row) => (
                <tr key={row.id} className="hover:bg-surface/60">
                  <td className="px-4 py-2 tabular-nums">{row.fecha}</td>
                  <td className="px-4 py-2 tabular-nums">{row.hora}</td>
                  <td className="px-4 py-2">{row.titulo}</td>
                  <td className="px-4 py-2">
                    <StatusBadge variant="neutral">{row.estado}</StatusBadge>
                  </td>
                  <td className="px-4 py-2">
                    {row.meet_url ? (
                      <a
                        href={row.meet_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-ink-700 underline"
                      >
                        Link
                      </a>
                    ) : (
                      "—"
                    )}
                  </td>
                </tr>
              ))}
              {(data ?? []).length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-text-secondary">
                    Sin encuentros.{" "}
                    <Link to="/encuentros/crear" className="font-medium text-ink-700 underline">
                      Crear el primero
                    </Link>
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
