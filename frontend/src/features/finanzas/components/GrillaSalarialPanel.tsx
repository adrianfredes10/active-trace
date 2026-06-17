import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import {
  fetchGrillaSalarial,
  guardarSalarioBase,
} from "@/features/finanzas/services/liquidacionService";

export function GrillaSalarialPanel() {
  const queryClient = useQueryClient();
  const [rol, setRol] = useState("PROFESOR");
  const [monto, setMonto] = useState("");

  const { data, isLoading, isError } = useQuery({
    queryKey: ["grilla-salarial"],
    queryFn: fetchGrillaSalarial,
    retry: false,
  });

  const guardarMutation = useMutation({
    mutationFn: () =>
      guardarSalarioBase({
        rol,
        monto,
        vig_desde: new Date().toISOString().slice(0, 10),
      }),
    onSuccess: () => {
      setMonto("");
      void queryClient.invalidateQueries({ queryKey: ["grilla-salarial"] });
    },
  });

  if (isError) {
    return (
      <p className="text-sm text-slate-600">
        Grilla salarial disponible cuando se implemente C-18 en backend.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      <form
        className="max-w-md space-y-3 rounded-lg border border-slate-200 bg-white p-4"
        onSubmit={(e) => {
          e.preventDefault();
          guardarMutation.mutate();
        }}
      >
        <h3 className="text-sm font-medium text-slate-800">Alta salario base</h3>
        <select
          aria-label="Rol"
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          value={rol}
          onChange={(e) => setRol(e.target.value)}
        >
          <option value="PROFESOR">PROFESOR</option>
          <option value="TUTOR">TUTOR</option>
          <option value="COORDINADOR">COORDINADOR</option>
        </select>
        <input
          aria-label="Monto"
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          value={monto}
          onChange={(e) => setMonto(e.target.value)}
          placeholder="150000.00"
        />
        <button
          type="submit"
          disabled={!monto || guardarMutation.isPending}
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-50"
        >
          Guardar
        </button>
      </form>

      {isLoading ? (
        <p className="text-sm text-slate-600">Cargando grilla…</p>
      ) : (
        <ul className="divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white text-sm">
          {(data ?? []).map((g) => (
            <li key={g.id} className="flex justify-between px-4 py-2">
              <span>{g.rol}</span>
              <span className="text-slate-600">${g.monto}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
