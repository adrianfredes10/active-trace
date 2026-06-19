import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import {
  fetchCarreras,
  fetchMaterias,
} from "@/features/admin/services/estructuraAdminService";
import { fetchCohortes } from "@/features/admin/services/profesorAdminService";
import { fetchUsuariosAdmin } from "@/features/admin/services/usuarioAdminService";
import type { ComisionContexto } from "@/features/coordinacion/types/coordinacion";
import { crearAsignacion } from "@/features/coordinacion/services/equiposCoordService";
import { Button } from "@/shared/components/ui/Button";
import { Dialog } from "@/shared/components/ui/Dialog";
import { Input } from "@/shared/components/ui/Input";
import { showToast } from "@/shared/components/ui/Toast";

type AsignacionFormDialogProps = {
  open: boolean;
  onClose: () => void;
  contexto: ComisionContexto;
  comisionInicial?: string;
};

const ROLES = ["PROFESOR", "TUTOR", "COORDINADOR", "NEXO"] as const;

export function AsignacionFormDialog({
  open,
  onClose,
  contexto,
  comisionInicial = "",
}: AsignacionFormDialogProps) {
  const queryClient = useQueryClient();
  const [usuarioId, setUsuarioId] = useState("");
  const [rol, setRol] = useState("PROFESOR");
  const [materiaId, setMateriaId] = useState(contexto.materia_id);
  const [carreraId, setCarreraId] = useState("");
  const [cohorteId, setCohorteId] = useState(contexto.cohorte_id);
  const [comisiones, setComisiones] = useState(comisionInicial);
  const [desde, setDesde] = useState(new Date().toISOString().slice(0, 10));

  const usuarios = useQuery({
    queryKey: ["admin-usuarios"],
    queryFn: fetchUsuariosAdmin,
    enabled: open,
  });
  const carreras = useQuery({ queryKey: ["admin-carreras"], queryFn: fetchCarreras, enabled: open });
  const materias = useQuery({ queryKey: ["admin-materias"], queryFn: fetchMaterias, enabled: open });
  const cohortes = useQuery({
    queryKey: ["admin-cohortes", carreraId],
    queryFn: () => fetchCohortes(carreraId || undefined),
    enabled: open && Boolean(carreraId),
  });

  useEffect(() => {
    if (!open) return;
    setMateriaId(contexto.materia_id);
    setCohorteId(contexto.cohorte_id);
    setCarreraId(contexto.carrera_id);
    setComisiones(comisionInicial);
  }, [open, contexto, comisionInicial]);

  const crearMutation = useMutation({
    mutationFn: crearAsignacion,
    onSuccess: () => {
      showToast("Asignación creada", "success");
      void queryClient.invalidateQueries({ queryKey: ["asignaciones"] });
      onClose();
    },
    onError: () => showToast("No se pudo crear la asignación", "error"),
  });

  const selectClass =
    "w-full rounded-md border border-border bg-surface-card px-3 py-2 text-sm text-text-primary";

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="Nueva asignación"
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button
            disabled={crearMutation.isPending}
            onClick={() => {
              if (!usuarioId || !rol || !desde) {
                showToast("Usuario, rol y fecha desde son obligatorios", "error");
                return;
              }
              crearMutation.mutate({
                usuario_id: usuarioId,
                rol,
                materia_id: materiaId || undefined,
                carrera_id: carreraId || undefined,
                cohorte_id: cohorteId || undefined,
                comisiones: comisiones
                  ? comisiones.split(",").map((c) => c.trim()).filter(Boolean)
                  : undefined,
                desde,
              });
            }}
          >
            {crearMutation.isPending ? "Guardando…" : "Guardar"}
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <div>
          <label className="mb-1 block text-xs font-medium text-text-secondary">Usuario</label>
          <select className={selectClass} value={usuarioId} onChange={(e) => setUsuarioId(e.target.value)}>
            <option value="">Seleccionar…</option>
            {(usuarios.data ?? []).map((u) => (
              <option key={u.id} value={u.id}>
                {u.apellidos}, {u.nombre}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-text-secondary">Rol</label>
          <select className={selectClass} value={rol} onChange={(e) => setRol(e.target.value)}>
            {ROLES.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-text-secondary">Materia</label>
          <select className={selectClass} value={materiaId} onChange={(e) => setMateriaId(e.target.value)}>
            <option value="">Seleccionar…</option>
            {(materias.data ?? []).map((m) => (
              <option key={m.id} value={m.id}>
                {m.codigo} — {m.nombre}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-text-secondary">Carrera</label>
          <select className={selectClass} value={carreraId} onChange={(e) => setCarreraId(e.target.value)}>
            <option value="">Seleccionar…</option>
            {(carreras.data ?? []).map((c) => (
              <option key={c.id} value={c.id}>
                {c.codigo} — {c.nombre}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-text-secondary">Cohorte</label>
          <select
            className={selectClass}
            value={cohorteId}
            onChange={(e) => setCohorteId(e.target.value)}
            disabled={!carreraId}
          >
            <option value="">Seleccionar…</option>
            {(cohortes.data ?? []).map((c) => (
              <option key={c.id} value={c.id}>
                {c.nombre}
              </option>
            ))}
          </select>
        </div>

        <Input
          label="Comisiones"
          value={comisiones}
          onChange={(e) => setComisiones(e.target.value)}
          placeholder="A, B (separadas por coma)"
        />

        <Input label="Vigente desde" type="date" value={desde} onChange={(e) => setDesde(e.target.value)} />
      </div>
    </Dialog>
  );
}
