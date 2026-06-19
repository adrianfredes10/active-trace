import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { useState } from "react";

import { PageHeader } from "@/features/admin/components/shared/PageHeader";
import { crearMateria, fetchMaterias } from "@/features/admin/services/estructuraAdminService";
import type { MateriaItem } from "@/features/admin/types/admin";
import { Button } from "@/shared/components/ui/Button";
import { Input } from "@/shared/components/ui/Input";

export function MateriasPanel() {
  const queryClient = useQueryClient();
  const [codigo, setCodigo] = useState("");
  const [nombre, setNombre] = useState("");
  const [feedback, setFeedback] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const materias = useQuery({
    queryKey: ["admin-materias"],
    queryFn: fetchMaterias,
    retry: 1,
  });

  const mutation = useMutation({
    mutationFn: crearMateria,
    onSuccess: () => {
      setSubmitError(null);
      setFeedback("Materia creada correctamente.");
      setCodigo("");
      setNombre("");
      void queryClient.invalidateQueries({ queryKey: ["admin-materias"] });
      void queryClient.invalidateQueries({ queryKey: ["admin-resumen"] });
    },
    onError: (error) => {
      setFeedback(null);
      setSubmitError(formatApiError(error));
    },
  });

  return (
    <div className="space-y-6">
      <PageHeader title="Materias" subtitle="Catálogo de materias del instituto." />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,20rem)_1fr]">
        <section className="rounded-lg border border-border bg-surface-card p-4 shadow-sm">
          <h3 className="mb-3 text-sm font-semibold text-text-primary">Nueva materia</h3>
          <form
            className="space-y-3"
            onSubmit={(e) => {
              e.preventDefault();
              const c = codigo.trim();
              const n = nombre.trim();
              if (!c || !n) {
                setFeedback(null);
                setSubmitError("Completá código y nombre.");
                return;
              }
              setSubmitError(null);
              setFeedback(null);
              mutation.mutate({ codigo: c, nombre: n });
            }}
          >
            <Input
              label="Código"
              value={codigo}
              onChange={(e) => setCodigo(e.target.value)}
              placeholder="MAT01"
              autoComplete="off"
            />
            <Input
              label="Nombre"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              placeholder="Matemática I"
              autoComplete="off"
            />
            <Button type="submit" className="w-full sm:w-auto" disabled={mutation.isPending}>
              {mutation.isPending ? "Guardando…" : "Crear materia"}
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

        <MateriaList loading={materias.isLoading} error={materias.isError} items={materias.data ?? []} />
      </div>
    </div>
  );
}

function MateriaList({
  loading,
  error,
  items,
}: {
  loading: boolean;
  error: boolean;
  items: MateriaItem[];
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
                <th className="px-4 py-2 font-medium">Código</th>
                <th className="px-4 py-2 font-medium">Nombre</th>
                <th className="px-4 py-2 font-medium">Estado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {items.map((e) => (
                <tr key={e.id} className="hover:bg-surface/60">
                  <td className="px-4 py-2 font-mono text-xs">{e.codigo}</td>
                  <td className="px-4 py-2">{e.nombre}</td>
                  <td className="px-4 py-2 text-text-secondary">{e.estado}</td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr>
                  <td colSpan={3} className="px-4 py-6 text-center text-text-secondary">
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
    if (error.response?.status === 409) return "Ya existe un registro con ese código.";
  }
  return "No se pudo guardar. Revisá los datos e intentá de nuevo.";
}
