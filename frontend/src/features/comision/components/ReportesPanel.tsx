import { useQuery } from "@tanstack/react-query";

import { useComisionContext } from "@/features/comision/hooks/ComisionProvider";
import {
  exportSinCorregir,
  fetchRanking,
  fetchReporteRapido,
} from "@/features/comision/services/analisisService";

export function ReportesPanel() {
  const { contexto } = useComisionContext();

  const reporte = useQuery({
    queryKey: ["reporte-rapido", contexto],
    queryFn: () => fetchReporteRapido(contexto!),
    enabled: Boolean(contexto),
  });

  const ranking = useQuery({
    queryKey: ["ranking", contexto],
    queryFn: () => fetchRanking(contexto!),
    enabled: Boolean(contexto),
  });

  if (!contexto) {
    return null;
  }

  async function handleExport() {
    const blob = await exportSinCorregir(contexto!);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "sin-corregir.txt";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-6">
      {reporte.data && (
        <div className="grid gap-3 sm:grid-cols-4">
          <Stat label="Alumnos" value={String(reporte.data.total_alumnos)} />
          <Stat label="Atrasados" value={String(reporte.data.total_atrasados)} />
          <Stat label="Actividades" value={String(reporte.data.total_actividades)} />
          <Stat
            label="Tasa aprobación"
            value={
              reporte.data.tasa_aprobacion_pct != null
                ? `${reporte.data.tasa_aprobacion_pct}%`
                : "—"
            }
          />
        </div>
      )}

      <div>
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-sm font-medium text-slate-800">Ranking por aprobadas</h3>
          <button
            type="button"
            className="text-sm text-slate-600 underline hover:text-slate-900"
            onClick={() => void handleExport()}
          >
            Exportar sin corregir
          </button>
        </div>
        {ranking.isLoading ? (
          <p className="text-sm text-slate-600">Cargando ranking…</p>
        ) : (
          <ul className="divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white text-sm">
            {(ranking.data ?? []).slice(0, 10).map((r) => (
              <li key={r.entrada_padron_id} className="flex justify-between px-4 py-2">
                <span>
                  {r.apellidos}, {r.nombre}
                </span>
                <span className="text-slate-600">{r.aprobadas} aprobadas</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-4 py-3">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="text-lg font-semibold text-slate-900">{value}</p>
    </div>
  );
}
