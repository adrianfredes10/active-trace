import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useCoordinacionContext } from "@/features/coordinacion/hooks/CoordinacionProvider";
import {
  exportarEquipoCsv,
  fetchAsignaciones,
} from "@/features/coordinacion/services/equiposCoordService";
import { ClonarEquipoForm } from "@/features/coordinacion/components/ClonarEquipoForm";

export function EquiposPanel() {
  const { contexto } = useCoordinacionContext();
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["asignaciones", contexto?.materia_id],
    queryFn: () => fetchAsignaciones(contexto!.materia_id),
    enabled: Boolean(contexto),
  });

  const exportMutation = useMutation({
    mutationFn: () =>
      exportarEquipoCsv(
        contexto!.materia_id,
        contexto!.carrera_id,
        contexto!.cohorte_id,
      ),
    onSuccess: (blob) => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "equipo_docente.csv";
      a.click();
      URL.revokeObjectURL(url);
    },
  });

  if (!contexto) {
    return null;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-slate-800">
          Asignaciones ({data?.length ?? 0})
        </h3>
        <button
          type="button"
          className="text-sm text-slate-600 underline hover:text-slate-900 disabled:opacity-50"
          disabled={exportMutation.isPending}
          onClick={() => exportMutation.mutate()}
        >
          Exportar CSV
        </button>
      </div>

      {isLoading ? (
        <p className="text-sm text-slate-600">Cargando equipo…</p>
      ) : (
        <ul className="divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white text-sm">
          {(data ?? []).map((a) => (
            <li key={a.id} className="flex justify-between px-4 py-2">
              <span>
                {a.rol} — usuario {a.usuario_id.slice(0, 8)}…
              </span>
              <span className={a.vigente ? "text-green-700" : "text-slate-400"}>
                {a.vigente ? "Vigente" : "Vencida"}
              </span>
            </li>
          ))}
        </ul>
      )}

      <ClonarEquipoForm
        contexto={contexto}
        onClonado={() => {
          void queryClient.invalidateQueries({ queryKey: ["asignaciones"] });
        }}
      />
    </div>
  );
}
