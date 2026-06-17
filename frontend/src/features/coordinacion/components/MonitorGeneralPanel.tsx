import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { useCoordinacionContext } from "@/features/coordinacion/hooks/CoordinacionProvider";
import { fetchMonitorGeneral } from "@/features/coordinacion/services/monitorService";

export function MonitorGeneralPanel() {
  const { contexto } = useCoordinacionContext();
  const [comision, setComision] = useState("");
  const [soloAtrasados, setSoloAtrasados] = useState(false);

  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ["monitor-general", contexto, comision, soloAtrasados],
    queryFn: () =>
      fetchMonitorGeneral({
        materia_id: contexto!.materia_id,
        cohorte_id: contexto!.cohorte_id,
        asignacion_id: contexto!.asignacion_id,
        comision: comision || undefined,
        solo_atrasados: soloAtrasados,
      }),
    enabled: Boolean(contexto),
  });

  if (!contexto) {
    return null;
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end gap-4 rounded-lg border border-slate-200 bg-white p-4">
        <div>
          <label htmlFor="filtro-comision" className="block text-sm text-slate-700">
            Comisión
          </label>
          <input
            id="filtro-comision"
            className="mt-1 rounded-lg border border-slate-300 px-3 py-2 text-sm"
            value={comision}
            onChange={(e) => setComision(e.target.value)}
            placeholder="A, B…"
          />
        </div>
        <label className="flex items-center gap-2 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={soloAtrasados}
            onChange={(e) => setSoloAtrasados(e.target.checked)}
          />
          Solo atrasados
        </label>
        <button
          type="button"
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm hover:bg-slate-50"
          onClick={() => void refetch()}
        >
          {isFetching ? "Filtrando…" : "Aplicar filtros"}
        </button>
      </div>

      {isLoading ? (
        <p className="text-sm text-slate-600">Cargando monitor…</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50 text-slate-600">
              <tr>
                <th className="px-4 py-2 font-medium">Alumno</th>
                <th className="px-4 py-2 font-medium">Comisión</th>
                <th className="px-4 py-2 font-medium">Aprobadas</th>
                <th className="px-4 py-2 font-medium">Atrasado</th>
              </tr>
            </thead>
            <tbody>
              {(data ?? []).map((row) => (
                <tr key={row.entrada_padron_id} className="border-b border-slate-100">
                  <td className="px-4 py-2">
                    {row.apellidos}, {row.nombre}
                  </td>
                  <td className="px-4 py-2">{row.comision ?? "—"}</td>
                  <td className="px-4 py-2">
                    {row.aprobadas}/{row.total_actividades}
                  </td>
                  <td className="px-4 py-2">{row.atrasado ? "Sí" : "No"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
