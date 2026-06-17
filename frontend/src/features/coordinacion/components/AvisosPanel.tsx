import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { AvisoPublicarForm } from "@/features/coordinacion/components/AvisoPublicarForm";
import { useCoordinacionContext } from "@/features/coordinacion/hooks/CoordinacionProvider";
import {
  eliminarAviso,
  fetchAvisosGestion,
} from "@/features/coordinacion/services/avisoService";

export function AvisosPanel() {
  const { contexto } = useCoordinacionContext();
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["avisos-gestion"],
    queryFn: fetchAvisosGestion,
  });

  const deleteMutation = useMutation({
    mutationFn: eliminarAviso,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["avisos-gestion"] });
    },
  });

  return (
    <div className="space-y-6">
      <AvisoPublicarForm
        contexto={contexto}
        onPublicado={() => {
          void queryClient.invalidateQueries({ queryKey: ["avisos-gestion"] });
        }}
      />

      <div>
        <h3 className="mb-2 text-sm font-medium text-slate-800">Avisos publicados</h3>
        {isLoading ? (
          <p className="text-sm text-slate-600">Cargando…</p>
        ) : (
          <ul className="divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white text-sm">
            {(data ?? []).map((a) => (
              <li key={a.id} className="flex items-start justify-between gap-4 px-4 py-3">
                <div>
                  <p className="font-medium text-slate-900">{a.titulo}</p>
                  <p className="text-xs text-slate-500">
                    {a.alcance} · {a.severidad} · {a.activo ? "Activo" : "Inactivo"}
                  </p>
                </div>
                <button
                  type="button"
                  className="text-xs text-red-600 hover:underline"
                  onClick={() => deleteMutation.mutate(a.id)}
                >
                  Eliminar
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
