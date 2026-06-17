import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useCoordinacionContext } from "@/features/coordinacion/hooks/CoordinacionProvider";
import {
  actualizarEstadoTarea,
  fetchTareasAdmin,
} from "@/features/coordinacion/services/tareaService";

const ESTADOS = ["Pendiente", "En progreso", "Resuelta", "Cancelada"] as const;

export function TareasPanel() {
  const { contexto } = useCoordinacionContext();
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["tareas-admin", contexto?.materia_id],
    queryFn: () => fetchTareasAdmin(contexto?.materia_id),
    enabled: Boolean(contexto),
  });

  const estadoMutation = useMutation({
    mutationFn: ({ id, estado }: { id: string; estado: string }) =>
      actualizarEstadoTarea(id, estado),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["tareas-admin"] });
    },
  });

  if (!contexto) {
    return null;
  }

  if (isLoading) {
    return <p className="text-sm text-slate-600">Cargando tareas…</p>;
  }

  return (
    <ul className="divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white text-sm">
      {(data ?? []).map((t) => (
        <li key={t.id} className="flex flex-col gap-2 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="font-medium text-slate-900">{t.descripcion}</p>
            <p className="text-xs text-slate-500">Estado: {t.estado}</p>
          </div>
          <select
            className="rounded-lg border border-slate-300 px-2 py-1 text-sm"
            value={t.estado}
            onChange={(e) =>
              estadoMutation.mutate({ id: t.id, estado: e.target.value })
            }
          >
            {ESTADOS.map((e) => (
              <option key={e} value={e}>
                {e}
              </option>
            ))}
          </select>
        </li>
      ))}
      {(data ?? []).length === 0 && (
        <li className="px-4 py-6 text-center text-slate-500">Sin tareas en esta materia.</li>
      )}
    </ul>
  );
}
