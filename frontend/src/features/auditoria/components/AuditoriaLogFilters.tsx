import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import {
  fetchAuditoriaLog,
  type AuditoriaLogFiltros,
} from "@/features/auditoria/services/auditoriaPanelService";

export function AuditoriaLogFilters() {
  const [materiaId, setMateriaId] = useState("");
  const [accion, setAccion] = useState("");
  const [limit, setLimit] = useState(200);
  const [filtros, setFiltros] = useState<AuditoriaLogFiltros>({ limit: 200 });

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ["auditoria-log", filtros],
    queryFn: () => fetchAuditoriaLog(filtros),
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end gap-3 rounded-lg border border-slate-200 bg-white p-4">
        <div>
          <label htmlFor="filtro-materia" className="block text-sm text-slate-700">
            Materia ID
          </label>
          <input
            id="filtro-materia"
            className="mt-1 rounded-lg border border-slate-300 px-3 py-2 text-sm"
            value={materiaId}
            onChange={(e) => setMateriaId(e.target.value)}
          />
        </div>
        <div>
          <label htmlFor="filtro-accion" className="block text-sm text-slate-700">
            Acción
          </label>
          <input
            id="filtro-accion"
            className="mt-1 rounded-lg border border-slate-300 px-3 py-2 text-sm"
            value={accion}
            onChange={(e) => setAccion(e.target.value)}
            placeholder="CALIFICACIONES_IMPORTAR"
          />
        </div>
        <div>
          <label htmlFor="filtro-limit" className="block text-sm text-slate-700">
            Límite
          </label>
          <input
            id="filtro-limit"
            type="number"
            min={1}
            max={500}
            className="mt-1 w-24 rounded-lg border border-slate-300 px-3 py-2 text-sm"
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
          />
        </div>
        <button
          type="button"
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm hover:bg-slate-50"
          onClick={() =>
            setFiltros({
              materia_id: materiaId || undefined,
              accion: accion || undefined,
              limit,
            })
          }
        >
          {isFetching ? "Filtrando…" : "Aplicar filtros"}
        </button>
      </div>

      {isLoading ? (
        <p className="text-sm text-slate-600">Cargando log…</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50 text-slate-600">
              <tr>
                <th className="px-4 py-2 font-medium">Fecha</th>
                <th className="px-4 py-2 font-medium">Acción</th>
                <th className="px-4 py-2 font-medium">Actor</th>
                <th className="px-4 py-2 font-medium">Filas</th>
              </tr>
            </thead>
            <tbody>
              {(data?.items ?? []).map((row) => (
                <tr key={row.id} className="border-b border-slate-100">
                  <td className="px-4 py-2 whitespace-nowrap">
                    {new Date(row.fecha_hora).toLocaleString()}
                  </td>
                  <td className="px-4 py-2 font-mono text-xs">{row.accion}</td>
                  <td className="px-4 py-2 font-mono text-xs text-slate-500">
                    {row.actor_id}
                  </td>
                  <td className="px-4 py-2">{row.filas_afectadas}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="border-t border-slate-100 px-4 py-2 text-xs text-slate-500">
            Mostrando {(data?.items ?? []).length} de límite {data?.limit ?? limit}
          </p>
        </div>
      )}
    </div>
  );
}
