import { useQuery } from "@tanstack/react-query";

import { useComisionContext } from "@/features/comision/hooks/ComisionProvider";
import { fetchAtrasados } from "@/features/comision/services/analisisService";

export function AtrasadosTable() {
  const { contexto } = useComisionContext();

  const { data, isLoading, isError } = useQuery({
    queryKey: ["atrasados", contexto],
    queryFn: () => fetchAtrasados(contexto!),
    enabled: Boolean(contexto),
  });

  if (!contexto) {
    return null;
  }

  if (isLoading) {
    return <p className="text-sm text-slate-600">Cargando atrasados…</p>;
  }

  if (isError) {
    return <p className="text-sm text-red-600">No se pudo cargar la lista de atrasados.</p>;
  }

  const items = data?.items ?? [];

  return (
    <div className="space-y-3">
      <p className="text-sm text-slate-600">
        {data?.total_atrasados ?? 0} atrasados de {data?.total_alumnos ?? 0} alumnos
      </p>
      {items.length === 0 ? (
        <p className="rounded-lg border border-dashed border-slate-300 px-4 py-6 text-center text-sm text-slate-500">
          Sin atrasados en esta comisión.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50 text-slate-600">
              <tr>
                <th className="px-4 py-2 font-medium">Alumno</th>
                <th className="px-4 py-2 font-medium">Email</th>
                <th className="px-4 py-2 font-medium">Comisión</th>
                <th className="px-4 py-2 font-medium">Motivos</th>
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr key={row.entrada_padron_id} className="border-b border-slate-100 last:border-0">
                  <td className="px-4 py-2">
                    {row.apellidos}, {row.nombre}
                  </td>
                  <td className="px-4 py-2 text-slate-600">{row.email}</td>
                  <td className="px-4 py-2">{row.comision ?? "—"}</td>
                  <td className="px-4 py-2 text-slate-600">{row.motivos.join(", ")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
