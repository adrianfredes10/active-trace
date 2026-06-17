import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { useState } from "react";

import {
  crearCarrera,
  crearMateria,
  fetchCarreras,
  fetchMaterias,
} from "@/features/admin/services/estructuraAdminService";

type EntityItem = { id: string; codigo: string; nombre: string; estado: string };

export function EstructuraPanel() {
  const queryClient = useQueryClient();

  const carreras = useQuery({
    queryKey: ["admin-carreras"],
    queryFn: fetchCarreras,
    retry: 1,
  });
  const materias = useQuery({
    queryKey: ["admin-materias"],
    queryFn: fetchMaterias,
    retry: 1,
  });

  return (
    <div className="space-y-8">
      <EntityCreateSection
        formId="form-carrera"
        title="Nueva carrera"
        submitLabel="Crear carrera"
        codigoLabel="Código carrera"
        nombreLabel="Nombre carrera"
        codigoPlaceholder="TUP"
        nombrePlaceholder="Tecnicatura Universitaria"
        onCreate={crearCarrera}
        onSuccess={() => {
          void queryClient.invalidateQueries({ queryKey: ["admin-carreras"] });
        }}
      />

      <EntityListSection
        title="Carreras"
        loading={carreras.isLoading}
        error={carreras.isError}
        items={carreras.data ?? []}
      />

      <EntityCreateSection
        formId="form-materia"
        title="Nueva materia"
        submitLabel="Crear materia"
        codigoLabel="Código materia"
        nombreLabel="Nombre materia"
        codigoPlaceholder="MAT01"
        nombrePlaceholder="Matemática I"
        onCreate={crearMateria}
        onSuccess={() => {
          void queryClient.invalidateQueries({ queryKey: ["admin-materias"] });
        }}
      />

      <EntityListSection
        title="Materias"
        loading={materias.isLoading}
        error={materias.isError}
        items={materias.data ?? []}
      />
    </div>
  );
}

function EntityCreateSection({
  formId,
  title,
  submitLabel,
  codigoLabel,
  nombreLabel,
  codigoPlaceholder,
  nombrePlaceholder,
  onCreate,
  onSuccess,
}: {
  formId: string;
  title: string;
  submitLabel: string;
  codigoLabel: string;
  nombreLabel: string;
  codigoPlaceholder: string;
  nombrePlaceholder: string;
  onCreate: (payload: { codigo: string; nombre: string }) => Promise<unknown>;
  onSuccess: () => void;
}) {
  const [feedback, setFeedback] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (payload: { codigo: string; nombre: string }) => onCreate(payload),
    onSuccess: () => {
      setSubmitError(null);
      setFeedback(`${submitLabel.replace("Crear ", "")} guardada correctamente.`);
      onSuccess();
    },
    onError: (error) => {
      setFeedback(null);
      setSubmitError(formatApiError(error));
    },
  });

  const codigoField = `${formId}-codigo`;
  const nombreField = `${formId}-nombre`;

  return (
    <section className="max-w-md rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="mb-3 text-sm font-semibold text-slate-800">{title}</h3>
      <form
        id={formId}
        className="space-y-3"
        onSubmit={(e) => {
          e.preventDefault();
          const form = e.currentTarget;
          const codigo = (form.elements.namedItem(codigoField) as HTMLInputElement).value.trim();
          const nombre = (form.elements.namedItem(nombreField) as HTMLInputElement).value.trim();
          if (!codigo || !nombre) {
            setFeedback(null);
            setSubmitError("Completá código y nombre.");
            return;
          }
          setSubmitError(null);
          setFeedback(null);
          mutation.mutate({ codigo, nombre });
          form.reset();
        }}
      >
        <label className="block text-xs font-medium text-slate-600" htmlFor={codigoField}>
          {codigoLabel}
        </label>
        <input
          id={codigoField}
          name={codigoField}
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          placeholder={codigoPlaceholder}
          autoComplete="off"
        />

        <label className="block text-xs font-medium text-slate-600" htmlFor={nombreField}>
          {nombreLabel}
        </label>
        <input
          id={nombreField}
          name={nombreField}
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          placeholder={nombrePlaceholder}
          autoComplete="off"
        />

        <button
          type="submit"
          className="mt-1 w-full cursor-pointer rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white hover:bg-slate-800"
        >
          {mutation.isPending ? "Guardando…" : submitLabel}
        </button>

        {submitError && (
          <p className="text-sm text-red-600" role="alert">
            {submitError}
          </p>
        )}
        {feedback && !submitError && (
          <p className="text-sm text-green-700" role="status">
            {feedback}
          </p>
        )}
      </form>
    </section>
  );
}

function EntityListSection({
  title,
  loading,
  error,
  items,
}: {
  title: string;
  loading: boolean;
  error: boolean;
  items: EntityItem[];
}) {
  return (
    <div>
      <h3 className="mb-2 text-sm font-medium text-slate-800">{title}</h3>
      {loading && <p className="text-sm text-slate-600">Cargando…</p>}
      {error && (
        <p className="text-sm text-red-600" role="alert">
          No se pudo cargar el listado. Verificá que la API esté en marcha.
        </p>
      )}
      {!loading && !error && (
        <ul className="divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white text-sm">
          {items.map((e) => (
            <li key={e.id} className="flex justify-between px-4 py-2">
              <span>
                {e.codigo} — {e.nombre}
              </span>
              <span className="text-slate-500">{e.estado}</span>
            </li>
          ))}
          {items.length === 0 && (
            <li className="px-4 py-4 text-center text-slate-500">Sin registros.</li>
          )}
        </ul>
      )}
    </div>
  );
}

function formatApiError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") {
      return detail;
    }
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0] as { msg?: string };
      if (typeof first.msg === "string") {
        return first.msg;
      }
    }
    if (error.response?.status === 403) {
      return "Sin permiso. Usá admin@demo.local.";
    }
    if (error.response?.status === 409) {
      return "Ya existe un registro con ese código.";
    }
  }
  return "No se pudo guardar. Revisá los datos e intentá de nuevo.";
}
