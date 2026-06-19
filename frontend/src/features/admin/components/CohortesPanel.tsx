import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { useState } from "react";

import { PageHeader } from "@/features/admin/components/shared/PageHeader";
import {
  crearCohorte,
  fetchCarreras,
  fetchCohortes,
} from "@/features/admin/services/estructuraAdminService";
import type { CohorteItem } from "@/features/admin/types/admin";
import { Button } from "@/shared/components/ui/Button";
import { Input } from "@/shared/components/ui/Input";

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

export function CohortesPanel() {
  const queryClient = useQueryClient();
  const [carreraId, setCarreraId] = useState("");
  const [nombre, setNombre] = useState("");
  const [anio, setAnio] = useState(String(new Date().getFullYear()));
  const [feedback, setFeedback] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const carreras = useQuery({ queryKey: ["admin-carreras"], queryFn: fetchCarreras, retry: 1 });
  const cohortes = useQuery({ queryKey: ["admin-cohortes"], queryFn: fetchCohortes, retry: 1 });

  const mutation = useMutation({
    mutationFn: crearCohorte,
    onSuccess: () => {
      setSubmitError(null);
      setFeedback("Cohorte creada correctamente.");
      setNombre("");
      void queryClient.invalidateQueries({ queryKey: ["admin-cohortes"] });
      void queryClient.invalidateQueries({ queryKey: ["admin-resumen"] });
    },
    onError: (error) => {
      setFeedback(null);
      setSubmitError(formatApiError(error));
    },
  });

  const carreraMap = new Map((carreras.data ?? []).map((c) => [c.id, c.codigo]));

  return (
    <div className="space-y-6">
      <PageHeader title="Cohortes" subtitle="Cohortes vinculadas a cada carrera." />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,20rem)_1fr]">
        <section className="rounded-lg border border-border bg-surface-card p-4 shadow-sm">
          <h3 className="mb-3 text-sm font-semibold text-text-primary">Nueva cohorte</h3>
          <form
            className="space-y-3"
            onSubmit={(e) => {
              e.preventDefault();
              const n = nombre.trim();
              const year = Number(anio);
              if (!carreraId || !n || !Number.isFinite(year)) {
                setFeedback(null);
                setSubmitError("Completá carrera, nombre y año.");
                return;
              }
              setSubmitError(null);
              setFeedback(null);
              mutation.mutate({
                carrera_id: carreraId,
                nombre: n,
                anio: year,
                vig_desde: todayIso(),
              });
            }}
          >
            <div>
              <label className="mb-1 block text-xs font-medium text-text-secondary" htmlFor="cohorte-carrera">
                Carrera
              </label>
              <select
                id="cohorte-carrera"
                value={carreraId}
                onChange={(e) => setCarreraId(e.target.value)}
                className="w-full rounded-md border border-border bg-surface-card px-3 py-2 text-sm focus-ring"
              >
                <option value="">Seleccionar…</option>
                {(carreras.data ?? []).map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.codigo} — {c.nombre}
                  </option>
                ))}
              </select>
            </div>
            <Input
              label="Nombre"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              placeholder="2026"
              autoComplete="off"
            />
            <Input
              label="Año"
              type="number"
              min={1900}
              max={2100}
              value={anio}
              onChange={(e) => setAnio(e.target.value)}
            />
            <Button type="submit" className="w-full sm:w-auto" disabled={mutation.isPending}>
              {mutation.isPending ? "Guardando…" : "Crear cohorte"}
            </Button>
            {submitError && (
              <p className="text-sm text-status-danger" role="alert">
                {submitError}
              </p>
            )}
            {feedback && !submitError && (
              <p className="text-sm text-emerald-700" role="status">
                {feedback}
              </p>
            )}
          </form>
        </section>

        <CohorteList
          loading={cohortes.isLoading}
          error={cohortes.isError}
          items={cohortes.data ?? []}
          carreraMap={carreraMap}
        />
      </div>
    </div>
  );
}

function CohorteList({
  loading,
  error,
  items,
  carreraMap,
}: {
  loading: boolean;
  error: boolean;
  items: CohorteItem[];
  carreraMap: Map<string, string>;
}) {
  return (
    <section>
      <h3 className="mb-2 text-sm font-medium text-text-primary">Listado</h3>
      {loading && <p className="text-sm text-text-secondary">Cargando…</p>}
      {error && (
        <p className="text-sm text-status-danger" role="alert">
          No se pudo cargar el listado.
        </p>
      )}
      {!loading && !error && (
        <div className="overflow-x-auto rounded-lg border border-border bg-surface-card">
          <table className="min-w-full text-sm">
            <thead className="border-b border-border bg-surface text-left text-xs uppercase tracking-wide text-text-secondary">
              <tr>
                <th className="px-4 py-2 font-medium">Carrera</th>
                <th className="px-4 py-2 font-medium">Nombre</th>
                <th className="px-4 py-2 font-medium">Año</th>
                <th className="px-4 py-2 font-medium">Estado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {items.map((e) => (
                <tr key={e.id} className="hover:bg-surface/60">
                  <td className="px-4 py-2 font-mono text-xs">{carreraMap.get(e.carrera_id) ?? "—"}</td>
                  <td className="px-4 py-2">{e.nombre}</td>
                  <td className="px-4 py-2 tabular-nums">{e.anio}</td>
                  <td className="px-4 py-2 text-text-secondary">{e.estado}</td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-4 py-6 text-center text-text-secondary">
                    Sin registros.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function formatApiError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (error.response?.status === 403) return "Sin permiso.";
    if (error.response?.status === 409) return "Ya existe una cohorte similar.";
  }
  return "No se pudo guardar. Revisá los datos e intentá de nuevo.";
}
