import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { useState } from "react";

import { fetchMisEquipos } from "@/features/comision/services/equipoService";
import type { AsignacionItem } from "@/features/comision/types/comision";
import { crearEncuentroUnico } from "@/features/encuentros/services/encuentroService";
import { Button } from "@/shared/components/ui/Button";
import { Input } from "@/shared/components/ui/Input";
import { showToast } from "@/shared/components/ui/Toast";

function labelAsignacion(item: AsignacionItem): string {
  const materia = item.materia_nombre ?? item.materia_codigo ?? "Materia";
  const comision = item.comisiones[0] ? ` · comisión ${item.comisiones[0]}` : "";
  return `${materia}${comision}`;
}

export function EncuentrosPage() {
  const queryClient = useQueryClient();
  const [asignacionId, setAsignacionId] = useState("");
  const [titulo, setTitulo] = useState("");
  const [fecha, setFecha] = useState(new Date().toISOString().slice(0, 10));
  const [hora, setHora] = useState("18:00");
  const [meetUrl, setMeetUrl] = useState("");
  const [error, setError] = useState<string | null>(null);

  const equipos = useQuery({
    queryKey: ["mis-equipos-encuentros"],
    queryFn: () => fetchMisEquipos(true),
  });

  const asignaciones = (equipos.data?.items ?? []).filter(
    (e) => e.materia_id && e.vigente,
  );

  const selected = asignaciones.find((a) => a.id === asignacionId);

  const mutation = useMutation({
    mutationFn: async () => {
      if (!selected?.materia_id || !titulo.trim()) {
        throw new Error("Elegí tu materia y completá el título.");
      }
      return crearEncuentroUnico({
        materia_id: selected.materia_id,
        asignacion_id: selected.id,
        titulo: titulo.trim(),
        fecha,
        hora: `${hora}:00`.slice(0, 8),
        meet_url: meetUrl || undefined,
      });
    },
    onSuccess: () => {
      showToast("Encuentro creado.");
      setTitulo("");
      setMeetUrl("");
      void queryClient.invalidateQueries({ queryKey: ["mis-equipos-encuentros"] });
    },
    onError: (err) => setError(formatError(err)),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-semibold uppercase tracking-wide text-text-primary">
          Crear encuentro
        </h1>
        <p className="mt-1 text-sm text-text-secondary">
          Programá una clase en vivo para tu materia y comisión.
        </p>
      </div>

      {equipos.isLoading && <p className="text-sm text-text-secondary">Cargando tus materias…</p>}
      {equipos.isError && (
        <p className="text-sm text-status-danger">No se pudieron cargar tus asignaciones.</p>
      )}

      {!equipos.isLoading && asignaciones.length === 0 && (
        <p className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          No tenés materias asignadas. Pedí al administrador que te vincule a una comisión.
        </p>
      )}

      {asignaciones.length > 0 && (
        <form
          className="max-w-lg space-y-4 rounded-lg border border-border bg-surface-card p-4"
          onSubmit={(e) => {
            e.preventDefault();
            setError(null);
            mutation.mutate();
          }}
        >
          <div>
            <label className="mb-1 block text-xs font-medium text-text-secondary" htmlFor="asignacion">
              Mi materia
            </label>
            <select
              id="asignacion"
              value={asignacionId}
              onChange={(e) => setAsignacionId(e.target.value)}
              className="w-full rounded-md border border-border bg-surface-card px-3 py-2 text-sm focus-ring"
            >
              <option value="">Seleccionar…</option>
              {asignaciones.map((a) => (
                <option key={a.id} value={a.id}>
                  {labelAsignacion(a)}
                </option>
              ))}
            </select>
          </div>

          <Input label="Título" value={titulo} onChange={(e) => setTitulo(e.target.value)} />
          <Input label="Fecha" type="date" value={fecha} onChange={(e) => setFecha(e.target.value)} />
          <Input label="Hora" type="time" value={hora} onChange={(e) => setHora(e.target.value)} />
          <Input
            label="Link de videollamada (opcional)"
            value={meetUrl}
            onChange={(e) => setMeetUrl(e.target.value)}
            placeholder="https://meet.google.com/..."
          />

          {error && (
            <p className="text-sm text-status-danger" role="alert">
              {error}
            </p>
          )}

          <Button type="submit" disabled={mutation.isPending || !asignacionId}>
            {mutation.isPending ? "Guardando…" : "Crear encuentro"}
          </Button>
        </form>
      )}
    </div>
  );
}

function formatError(err: unknown): string {
  if (err instanceof Error) return err.message;
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail;
    if (typeof detail === "string") return detail;
  }
  return "No se pudo crear el encuentro.";
}
