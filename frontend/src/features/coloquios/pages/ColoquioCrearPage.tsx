import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { PageHeader } from "@/features/admin/components/shared/PageHeader";
import { fetchCohortes, fetchMaterias } from "@/features/admin/services/estructuraAdminService";
import { crearConvocatoria } from "@/features/coloquios/services/coloquioService";
import { Button } from "@/shared/components/ui/Button";
import { Input } from "@/shared/components/ui/Input";
import { showToast } from "@/shared/components/ui/Toast";

export function ColoquioCrearPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [materiaId, setMateriaId] = useState("");
  const [cohorteId, setCohorteId] = useState("");
  const [instancia, setInstancia] = useState("");
  const [fecha, setFecha] = useState(new Date().toISOString().slice(0, 10));
  const [hora, setHora] = useState("10:00");
  const [cupo, setCupo] = useState("20");
  const [error, setError] = useState<string | null>(null);

  const materias = useQuery({ queryKey: ["admin-materias"], queryFn: fetchMaterias });
  const cohortes = useQuery({ queryKey: ["admin-cohortes"], queryFn: fetchCohortes });

  const mutation = useMutation({
    mutationFn: () => {
      if (!materiaId || !cohorteId || !instancia.trim()) {
        throw new Error("Completá materia, cohorte e instancia.");
      }
      return crearConvocatoria({
        materia_id: materiaId,
        cohorte_id: cohorteId,
        instancia: instancia.trim(),
        turnos: [
          {
            fecha,
            hora: `${hora}:00`.slice(0, 8),
            cupo_max: Number(cupo),
          },
        ],
      });
    },
    onSuccess: (data) => {
      void queryClient.invalidateQueries({ queryKey: ["coloquios-convocatorias"] });
      void queryClient.invalidateQueries({ queryKey: ["coloquios-metricas"] });
      showToast("Convocatoria creada.");
      navigate(`/coloquios/${data.id}`);
    },
    onError: (err) => setError(formatError(err)),
  });

  return (
    <div className="space-y-6">
      <PageHeader title="Nueva convocatoria" subtitle="Coloquio con al menos un turno." />

      <form
        className="max-w-lg space-y-4 rounded-lg border border-border bg-surface-card p-4"
        onSubmit={(e) => {
          e.preventDefault();
          setError(null);
          mutation.mutate();
        }}
      >
        <div>
          <label className="mb-1 block text-xs font-medium text-text-secondary">Materia</label>
          <select
            value={materiaId}
            onChange={(e) => setMateriaId(e.target.value)}
            className="w-full rounded-md border border-border px-3 py-2 text-sm focus-ring"
          >
            <option value="">Seleccionar…</option>
            {(materias.data ?? []).map((m) => (
              <option key={m.id} value={m.id}>
                {m.codigo} — {m.nombre}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-text-secondary">Cohorte</label>
          <select
            value={cohorteId}
            onChange={(e) => setCohorteId(e.target.value)}
            className="w-full rounded-md border border-border px-3 py-2 text-sm focus-ring"
          >
            <option value="">Seleccionar…</option>
            {(cohortes.data ?? []).map((c) => (
              <option key={c.id} value={c.id}>
                {c.nombre} ({c.anio})
              </option>
            ))}
          </select>
        </div>
        <Input label="Instancia" value={instancia} onChange={(e) => setInstancia(e.target.value)} placeholder="1er llamado" />
        <Input label="Fecha turno" type="date" value={fecha} onChange={(e) => setFecha(e.target.value)} />
        <Input label="Hora" type="time" value={hora} onChange={(e) => setHora(e.target.value)} />
        <Input label="Cupo máximo" type="number" min={1} value={cupo} onChange={(e) => setCupo(e.target.value)} />

        {error && (
          <p className="text-sm text-status-danger" role="alert">
            {error}
          </p>
        )}

        <div className="flex gap-2">
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? "Creando…" : "Crear convocatoria"}
          </Button>
          <Link
            to="/coloquios"
            className="inline-flex h-10 items-center rounded-md border border-border px-4 text-sm no-underline hover:bg-surface"
          >
            Cancelar
          </Link>
        </div>
      </form>
    </div>
  );
}

function formatError(err: unknown): string {
  if (err instanceof Error) return err.message;
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail;
    if (typeof detail === "string") return detail;
  }
  return "No se pudo crear la convocatoria.";
}
