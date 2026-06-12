import { useQuery } from "@tanstack/react-query";

import { fetchAuditLogs } from "@/features/auditoria/services/auditService";

export function AuditoriaPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["audit-logs"],
    queryFn: () => fetchAuditLogs(100),
  });

  if (isLoading) {
    return <p className="text-slate-600">Cargando auditoría…</p>;
  }

  if (isError) {
    return <p className="text-red-600">No se pudo cargar el log de auditoría.</p>;
  }

  const items = data?.items ?? [];

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Auditoría</h1>
        <p className="mt-1 text-sm text-slate-600">
          Últimas {items.length} entradas append-only (E-AUD).
        </p>
      </div>

      {items.length === 0 ? (
        <p className="rounded-lg border border-dashed border-slate-300 px-4 py-8 text-center text-sm text-slate-500">
          Sin registros todavía. Las acciones del sistema aparecerán acá.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50 text-slate-600">
              <tr>
                <th className="px-4 py-2 font-medium">Fecha</th>
                <th className="px-4 py-2 font-medium">Acción</th>
                <th className="px-4 py-2 font-medium">Actor</th>
                <th className="px-4 py-2 font-medium">Impersonado</th>
                <th className="px-4 py-2 font-medium">Filas</th>
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr key={row.id} className="border-b border-slate-100 last:border-0">
                  <td className="px-4 py-2 whitespace-nowrap text-slate-700">
                    {new Date(row.fecha_hora).toLocaleString()}
                  </td>
                  <td className="px-4 py-2 font-mono text-xs">{row.accion}</td>
                  <td className="px-4 py-2 font-mono text-xs text-slate-500">{row.actor_id}</td>
                  <td className="px-4 py-2 font-mono text-xs text-slate-500">
                    {row.impersonado_id ?? "—"}
                  </td>
                  <td className="px-4 py-2">{row.filas_afectadas}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
