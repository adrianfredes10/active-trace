import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { useComisionContext } from "@/features/comision/hooks/ComisionProvider";
import { fetchUmbral, guardarUmbral } from "@/features/comision/services/calificacionService";

export function UmbralPanel() {
  const { contexto } = useComisionContext();
  const queryClient = useQueryClient();
  const [umbralPct, setUmbralPct] = useState(60);
  const [valores, setValores] = useState("Satisfactorio,Aprobado");

  const { data, isLoading } = useQuery({
    queryKey: ["umbral", contexto?.asignacion_id],
    queryFn: () => fetchUmbral(contexto!.asignacion_id),
    enabled: Boolean(contexto),
  });

  useEffect(() => {
    if (data) {
      setUmbralPct(data.umbral_pct);
      setValores(data.valores_aprobatorios.join(","));
    }
  }, [data]);

  const saveMutation = useMutation({
    mutationFn: () =>
      guardarUmbral(
        contexto!,
        umbralPct,
        valores.split(",").map((v) => v.trim()).filter(Boolean),
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["umbral", contexto?.asignacion_id] });
    },
  });

  if (!contexto) {
    return null;
  }

  if (isLoading) {
    return <p className="text-sm text-slate-600">Cargando umbral…</p>;
  }

  return (
    <form
      className="max-w-md space-y-4 rounded-lg border border-slate-200 bg-white p-4"
      onSubmit={(e) => {
        e.preventDefault();
        saveMutation.mutate();
      }}
    >
      <div>
        <label className="block text-sm font-medium text-slate-700" htmlFor="umbral-pct">
          Umbral de aprobación (%)
        </label>
        <input
          id="umbral-pct"
          type="number"
          min={0}
          max={100}
          className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          value={umbralPct}
          onChange={(e) => setUmbralPct(Number(e.target.value))}
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-slate-700" htmlFor="valores-aprob">
          Valores textuales aprobatorios (coma)
        </label>
        <input
          id="valores-aprob"
          type="text"
          className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          value={valores}
          onChange={(e) => setValores(e.target.value)}
        />
      </div>
      <button
        type="submit"
        disabled={saveMutation.isPending}
        className="rounded-lg bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-50"
      >
        {saveMutation.isPending ? "Guardando…" : "Guardar umbral"}
      </button>
    </form>
  );
}
