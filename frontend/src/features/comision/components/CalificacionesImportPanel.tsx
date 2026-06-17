import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import { useComisionContext } from "@/features/comision/hooks/ComisionProvider";
import {
  importarCalificaciones,
  previewCalificaciones,
} from "@/features/comision/services/calificacionService";
import type { ActividadDetectada } from "@/features/comision/types/comision";

export function CalificacionesImportPanel() {
  const { contexto } = useComisionContext();
  const [file, setFile] = useState<File | null>(null);
  const [actividades, setActividades] = useState<ActividadDetectada[]>([]);
  const [seleccionadas, setSeleccionadas] = useState<Set<string>>(new Set());
  const [mensaje, setMensaje] = useState<string | null>(null);

  const previewMutation = useMutation({
    mutationFn: (f: File) => previewCalificaciones(f),
    onSuccess: (data) => {
      setActividades(data.actividades);
      setSeleccionadas(new Set(data.actividades.map((a) => a.nombre)));
      setMensaje(`Preview: ${data.total_filas} filas detectadas.`);
    },
    onError: () => setMensaje("Error al analizar el archivo."),
  });

  const importMutation = useMutation({
    mutationFn: () =>
      importarCalificaciones(contexto!, [...seleccionadas], file!),
    onSuccess: (data) => setMensaje(`Importadas ${data.importadas} calificaciones.`),
    onError: () => setMensaje("Error al importar calificaciones."),
  });

  if (!contexto) {
    return null;
  }

  function toggleActividad(nombre: string) {
    setSeleccionadas((prev) => {
      const next = new Set(prev);
      if (next.has(nombre)) {
        next.delete(nombre);
      } else {
        next.add(nombre);
      }
      return next;
    });
  }

  return (
    <div className="space-y-4 rounded-lg border border-slate-200 bg-white p-4">
      <div>
        <label htmlFor="calif-csv" className="block text-sm font-medium text-slate-700">
          Archivo CSV
        </label>
        <input
          id="calif-csv"
          type="file"
          accept=".csv"
          className="mt-1 block w-full text-sm"
          onChange={(e) => {
            const f = e.target.files?.[0] ?? null;
            setFile(f);
            setActividades([]);
            setMensaje(null);
          }}
        />
      </div>
      <button
        type="button"
        disabled={!file || previewMutation.isPending}
        className="rounded-lg bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-50"
        onClick={() => file && previewMutation.mutate(file)}
      >
        {previewMutation.isPending ? "Analizando…" : "Preview"}
      </button>

      {actividades.length > 0 && (
        <fieldset className="space-y-2">
          <legend className="text-sm font-medium text-slate-700">Actividades a importar</legend>
          {actividades.map((a) => (
            <label key={a.nombre} className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={seleccionadas.has(a.nombre)}
                onChange={() => toggleActividad(a.nombre)}
              />
              {a.nombre} <span className="text-slate-500">({a.tipo})</span>
            </label>
          ))}
        </fieldset>
      )}

      <button
        type="button"
        disabled={!file || seleccionadas.size === 0 || importMutation.isPending}
        className="rounded-lg border border-slate-300 px-4 py-2 text-sm hover:bg-slate-50 disabled:opacity-50"
        onClick={() => importMutation.mutate()}
      >
        {importMutation.isPending ? "Importando…" : "Importar seleccionadas"}
      </button>

      {mensaje && <p className="text-sm text-slate-600">{mensaje}</p>}
    </div>
  );
}
