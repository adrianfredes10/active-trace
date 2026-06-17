import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import { clonarEquipo } from "@/features/coordinacion/services/equiposCoordService";
import type { ComisionContexto } from "@/features/coordinacion/types/coordinacion";

type ClonarEquipoFormProps = {
  contexto: ComisionContexto;
  onClonado: () => void;
};

export function ClonarEquipoForm({ contexto, onClonado }: ClonarEquipoFormProps) {
  const [destinoCohorteId, setDestinoCohorteId] = useState("");
  const [mensaje, setMensaje] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () =>
      clonarEquipo({
        origen: {
          materia_id: contexto.materia_id,
          carrera_id: contexto.carrera_id,
          cohorte_id: contexto.cohorte_id,
        },
        destino: {
          materia_id: contexto.materia_id,
          carrera_id: contexto.carrera_id,
          cohorte_id: destinoCohorteId,
        },
        desde: new Date().toISOString().slice(0, 10),
      }),
    onSuccess: (data) => {
      setMensaje(`Clonadas ${data.creadas} asignaciones.`);
      onClonado();
    },
    onError: () => setMensaje("No se pudo clonar el equipo."),
  });

  return (
    <form
      className="max-w-md space-y-3 rounded-lg border border-slate-200 bg-white p-4"
      onSubmit={(e) => {
        e.preventDefault();
        if (!destinoCohorteId) {
          return;
        }
        mutation.mutate();
      }}
    >
      <h3 className="text-sm font-medium text-slate-800">Clonar equipo a otra cohorte</h3>
      <div>
        <label htmlFor="dest-cohorte" className="block text-sm text-slate-700">
          UUID cohorte destino
        </label>
        <input
          id="dest-cohorte"
          className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          value={destinoCohorteId}
          onChange={(e) => setDestinoCohorteId(e.target.value)}
          placeholder="cohorte-destino-uuid"
        />
      </div>
      <button
        type="submit"
        disabled={!destinoCohorteId || mutation.isPending}
        className="rounded-lg bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-50"
      >
        {mutation.isPending ? "Clonando…" : "Clonar equipo"}
      </button>
      {mensaje && <p className="text-sm text-slate-600">{mensaje}</p>}
    </form>
  );
}
