import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import { crearAviso } from "@/features/coordinacion/services/avisoService";
import type { ComisionContexto } from "@/features/coordinacion/types/coordinacion";

type AvisoPublicarFormProps = {
  contexto: ComisionContexto | null;
  onPublicado: () => void;
};

export function AvisoPublicarForm({ contexto, onPublicado }: AvisoPublicarFormProps) {
  const [titulo, setTitulo] = useState("Aviso de coordinación");
  const [cuerpo, setCuerpo] = useState("Mensaje institucional para el equipo docente.");
  const [mensaje, setMensaje] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () =>
      crearAviso({
        alcance: contexto ? "PorMateria" : "Global",
        materia_id: contexto?.materia_id ?? null,
        cohorte_id: contexto?.cohorte_id ?? null,
        severidad: "Info",
        titulo,
        cuerpo,
        inicio_en: new Date().toISOString(),
        requiere_ack: true,
      }),
    onSuccess: () => {
      setMensaje("Aviso publicado.");
      onPublicado();
    },
    onError: () => setMensaje("Error al publicar el aviso."),
  });

  return (
    <form
      className="max-w-lg space-y-3 rounded-lg border border-slate-200 bg-white p-4"
      onSubmit={(e) => {
        e.preventDefault();
        mutation.mutate();
      }}
    >
      <h3 className="text-sm font-medium text-slate-800">Publicar aviso</h3>
      <div>
        <label htmlFor="aviso-titulo" className="block text-sm text-slate-700">
          Título
        </label>
        <input
          id="aviso-titulo"
          className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          value={titulo}
          onChange={(e) => setTitulo(e.target.value)}
        />
      </div>
      <div>
        <label htmlFor="aviso-cuerpo" className="block text-sm text-slate-700">
          Cuerpo
        </label>
        <textarea
          id="aviso-cuerpo"
          rows={3}
          className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          value={cuerpo}
          onChange={(e) => setCuerpo(e.target.value)}
        />
      </div>
      <button
        type="submit"
        disabled={mutation.isPending}
        className="rounded-lg bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-50"
      >
        {mutation.isPending ? "Publicando…" : "Publicar"}
      </button>
      {mensaje && <p className="text-sm text-slate-600">{mensaje}</p>}
    </form>
  );
}
