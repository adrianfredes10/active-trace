import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { AsignacionFormDialog } from "@/features/coordinacion/components/AsignacionFormDialog";
import { ClonarEquipoForm } from "@/features/coordinacion/components/ClonarEquipoForm";
import { useCoordinacionContext } from "@/features/coordinacion/hooks/CoordinacionProvider";
import {
  exportarEquipoCsv,
  fetchAsignaciones,
} from "@/features/coordinacion/services/equiposCoordService";
import { Button } from "@/shared/components/ui/Button";

export function EquiposPanel() {
  const { contexto, selected } = useCoordinacionContext();
  const queryClient = useQueryClient();
  const [asignacionOpen, setAsignacionOpen] = useState(false);

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
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-medium text-text-primary">
          Asignaciones ({data?.length ?? 0})
        </h3>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" onClick={() => setAsignacionOpen(true)}>
            Nueva asignación
          </Button>
          <Button
            variant="ghost"
            size="sm"
            disabled={exportMutation.isPending}
            onClick={() => exportMutation.mutate()}
          >
            Exportar CSV
          </Button>
        </div>
      </div>

      {isLoading ? (
        <p className="text-sm text-text-secondary">Cargando equipo…</p>
      ) : (
        <ul className="divide-y divide-border rounded-lg border border-border bg-surface-card text-sm">
          {(data ?? []).map((a) => (
            <li key={a.id} className="flex justify-between px-4 py-2">
              <span>
                {a.rol} — com. {a.comisiones?.join(", ") || "—"} — usuario {a.usuario_id.slice(0, 8)}…
              </span>
              <span className={a.vigente ? "text-status-success" : "text-text-secondary"}>
                {a.vigente ? "Vigente" : "Vencida"}
              </span>
            </li>
          ))}
          {(data ?? []).length === 0 && (
            <li className="px-4 py-4 text-center text-text-secondary">Sin asignaciones.</li>
          )}
        </ul>
      )}

      <AsignacionFormDialog
        open={asignacionOpen}
        onClose={() => setAsignacionOpen(false)}
        contexto={contexto}
        comisionInicial={selected?.comisiones?.join(", ") ?? ""}
      />

      <ClonarEquipoForm
        contexto={contexto}
        onClonado={() => {
          void queryClient.invalidateQueries({ queryKey: ["asignaciones"] });
        }}
      />
    </div>
  );
}
