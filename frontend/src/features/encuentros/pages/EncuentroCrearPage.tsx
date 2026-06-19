import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { PageHeader } from "@/features/admin/components/shared/PageHeader";
import { fetchMaterias } from "@/features/admin/services/estructuraAdminService";
import { fetchAsignaciones } from "@/features/coordinacion/services/equiposCoordService";
import {
  crearEncuentroRecurrente,
  crearEncuentroUnico,
} from "@/features/encuentros/services/encuentroService";
import { DIAS_SEMANA } from "@/features/encuentros/types/encuentros";
import { Button } from "@/shared/components/ui/Button";
import { Input } from "@/shared/components/ui/Input";
import { showToast } from "@/shared/components/ui/Toast";

type Modo = "unico" | "recurrente";

export function EncuentroCrearPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [modo, setModo] = useState<Modo>("unico");
  const [materiaId, setMateriaId] = useState("");
  const [asignacionId, setAsignacionId] = useState("");
  const [titulo, setTitulo] = useState("");
  const [fecha, setFecha] = useState(new Date().toISOString().slice(0, 10));
  const [hora, setHora] = useState("18:00");
  const [diaSemana, setDiaSemana] = useState<string>(DIAS_SEMANA[0]);
  const [cantSemanas, setCantSemanas] = useState("8");
  const [meetUrl, setMeetUrl] = useState("");
  const [error, setError] = useState<string | null>(null);

  const materias = useQuery({ queryKey: ["admin-materias"], queryFn: fetchMaterias });
  const asignaciones = useQuery({
    queryKey: ["asignaciones", materiaId],
    queryFn: () => fetchAsignaciones(materiaId),
    enabled: Boolean(materiaId),
  });

  const mutation = useMutation({
    mutationFn: async () => {
      if (!materiaId || !asignacionId || !titulo.trim()) {
        throw new Error("Completá materia, asignación y título.");
      }
      if (modo === "unico") {
        return crearEncuentroUnico({
          materia_id: materiaId,
          asignacion_id: asignacionId,
          titulo: titulo.trim(),
          fecha,
          hora: `${hora}:00`.slice(0, 8),
          meet_url: meetUrl || undefined,
        });
      }
      return crearEncuentroRecurrente({
        materia_id: materiaId,
        asignacion_id: asignacionId,
        titulo: titulo.trim(),
        hora: `${hora}:00`.slice(0, 8),
        dia_semana: diaSemana,
        fecha_inicio: fecha,
        cant_semanas: Number(cantSemanas),
        vig_desde: fecha,
        meet_url: meetUrl || undefined,
      });
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["encuentros-admin"] });
      showToast("Encuentro creado correctamente.");
      navigate("/encuentros");
    },
    onError: (err) => {
      setError(formatError(err));
    },
  });

  return (
    <div className="space-y-6">
      <PageHeader title="Crear encuentro" subtitle="Encuentro único o serie recurrente." />

      <div className="flex flex-wrap gap-2">
        {(["unico", "recurrente"] as const).map((m) => (
          <button
            key={m}
            type="button"
            onClick={() => setModo(m)}
            className={`focus-ring rounded-md px-3 py-2 text-sm font-medium ${
              modo === m ? "bg-ink-900 text-white" : "border border-border bg-surface-card text-text-secondary"
            }`}
          >
            {m === "unico" ? "Único" : "Recurrente"}
          </button>
        ))}
      </div>

      <form
        className="max-w-lg space-y-4 rounded-lg border border-border bg-surface-card p-4"
        onSubmit={(e) => {
          e.preventDefault();
          setError(null);
          mutation.mutate();
        }}
      >
        <div>
          <label className="mb-1 block text-xs font-medium text-text-secondary" htmlFor="materia">
            Materia
          </label>
          <select
            id="materia"
            value={materiaId}
            onChange={(e) => {
              setMateriaId(e.target.value);
              setAsignacionId("");
            }}
            className="w-full rounded-md border border-border bg-surface-card px-3 py-2 text-sm focus-ring"
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
          <label className="mb-1 block text-xs font-medium text-text-secondary" htmlFor="asignacion">
            Asignación docente
          </label>
          <select
            id="asignacion"
            value={asignacionId}
            onChange={(e) => setAsignacionId(e.target.value)}
            disabled={!materiaId}
            className="w-full rounded-md border border-border bg-surface-card px-3 py-2 text-sm focus-ring disabled:opacity-50"
          >
            <option value="">Seleccionar…</option>
            {(asignaciones.data ?? []).map((a) => (
              <option key={a.id} value={a.id}>
                {a.rol} · {a.id.slice(0, 8)}…
              </option>
            ))}
          </select>
        </div>

        <Input label="Título" value={titulo} onChange={(e) => setTitulo(e.target.value)} />

        {modo === "unico" ? (
          <Input label="Fecha" type="date" value={fecha} onChange={(e) => setFecha(e.target.value)} />
        ) : (
          <>
            <Input
              label="Fecha inicio"
              type="date"
              value={fecha}
              onChange={(e) => setFecha(e.target.value)}
            />
            <div>
              <label className="mb-1 block text-xs font-medium text-text-secondary" htmlFor="dia">
                Día de la semana
              </label>
              <select
                id="dia"
                value={diaSemana}
                onChange={(e) => setDiaSemana(e.target.value)}
                className="w-full rounded-md border border-border px-3 py-2 text-sm focus-ring"
              >
                {DIAS_SEMANA.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            </div>
            <Input
              label="Cantidad de semanas"
              type="number"
              min={1}
              max={52}
              value={cantSemanas}
              onChange={(e) => setCantSemanas(e.target.value)}
            />
          </>
        )}

        <Input label="Hora" type="time" value={hora} onChange={(e) => setHora(e.target.value)} />
        <Input
          label="URL Meet (opcional)"
          value={meetUrl}
          onChange={(e) => setMeetUrl(e.target.value)}
          placeholder="https://meet.google.com/..."
        />

        {error && (
          <p className="text-sm text-status-danger" role="alert">
            {error}
          </p>
        )}

        <div className="flex flex-wrap gap-2">
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? "Guardando…" : "Crear"}
          </Button>
          <Link
            to="/encuentros"
            className="inline-flex h-10 items-center rounded-md border border-border px-4 text-sm text-text-primary no-underline hover:bg-surface"
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
  return "No se pudo crear el encuentro.";
}
