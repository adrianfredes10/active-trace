import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { useState } from "react";

import {
  crearProfesorCompleto,
  fetchCohortes,
} from "@/features/admin/services/profesorAdminService";
import {
  fetchCarreras,
  fetchMaterias,
} from "@/features/admin/services/estructuraAdminService";

function formatApiError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail.map((d) => d.msg ?? String(d)).join(", ");
  }
  return "No se pudo completar la operación.";
}

export function ProfesorAltaPanel() {
  const queryClient = useQueryClient();
  const [carreraId, setCarreraId] = useState("");
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);

  const carreras = useQuery({ queryKey: ["admin-carreras"], queryFn: fetchCarreras });
  const materias = useQuery({ queryKey: ["admin-materias"], queryFn: fetchMaterias });
  const cohortes = useQuery({
    queryKey: ["admin-cohortes", carreraId],
    queryFn: () => fetchCohortes(carreraId || undefined),
    enabled: Boolean(carreraId),
  });

  const crearMutation = useMutation({
    mutationFn: crearProfesorCompleto,
    onSuccess: (result) => {
      setSubmitError(null);
      setFeedback(
        `Profesor creado (${result.usuario.id}). Asignación ${result.asignacion_id} — comisión ${result.comision}.`,
      );
      void queryClient.invalidateQueries({ queryKey: ["admin-usuarios"] });
    },
    onError: (error) => {
      setFeedback(null);
      setSubmitError(formatApiError(error));
    },
  });

  return (
    <section className="max-w-lg rounded-lg border border-border bg-surface-card p-4">
      <h3 className="mb-1 text-sm font-semibold text-text-primary">Alta de profesor</h3>
      <p className="mb-4 text-xs text-text-secondary">
        Crea la cuenta, asigna rol PROFESOR y vincula materia + cohorte + comisión.
      </p>
      <form
        className="space-y-3"
        onSubmit={(e) => {
          e.preventDefault();
          const form = e.currentTarget;
          const email = (form.elements.namedItem("prof-email") as HTMLInputElement).value.trim();
          const password = (form.elements.namedItem("prof-password") as HTMLInputElement).value;
          const nombre = (form.elements.namedItem("prof-nombre") as HTMLInputElement).value.trim();
          const apellidos = (form.elements.namedItem("prof-apellidos") as HTMLInputElement).value.trim();
          const materiaId = (form.elements.namedItem("prof-materia") as HTMLSelectElement).value;
          const cohorteId = (form.elements.namedItem("prof-cohorte") as HTMLSelectElement).value;
          const comision = (form.elements.namedItem("prof-comision") as HTMLInputElement).value.trim();

          if (!email || password.length < 8 || !materiaId || !carreraId || !cohorteId || !comision) {
            setFeedback(null);
            setSubmitError("Completá email, contraseña (8+), carrera, cohorte, materia y comisión.");
            return;
          }

          setSubmitError(null);
          setFeedback(null);
          crearMutation.mutate({
            email,
            password,
            nombre: nombre || undefined,
            apellidos: apellidos || undefined,
            materia_id: materiaId,
            carrera_id: carreraId,
            cohorte_id: cohorteId,
            comision,
          });
          form.reset();
          setCarreraId("");
        }}
      >
        <Field label="Email institucional" id="prof-email" type="email" placeholder="profesor@instituto.edu" />
        <Field label="Contraseña inicial" id="prof-password" type="password" placeholder="Mínimo 8 caracteres" />
        <div className="grid grid-cols-2 gap-3">
          <Field label="Nombre" id="prof-nombre" placeholder="María" />
          <Field label="Apellidos" id="prof-apellidos" placeholder="García" />
        </div>

        <label className="block text-xs font-medium text-text-secondary" htmlFor="prof-carrera">
          Carrera
        </label>
        <select
          id="prof-carrera"
          className="w-full rounded-md border border-border bg-surface-card px-3 py-2 text-sm"
          value={carreraId}
          onChange={(e) => setCarreraId(e.target.value)}
        >
          <option value="">Seleccionar…</option>
          {(carreras.data ?? []).map((c) => (
            <option key={c.id} value={c.id}>
              {c.codigo} — {c.nombre}
            </option>
          ))}
        </select>

        <label className="block text-xs font-medium text-text-secondary" htmlFor="prof-cohorte">
          Cohorte
        </label>
        <select
          id="prof-cohorte"
          name="prof-cohorte"
          className="w-full rounded-md border border-border bg-surface-card px-3 py-2 text-sm"
          disabled={!carreraId}
        >
          <option value="">Seleccionar…</option>
          {(cohortes.data ?? []).map((c) => (
            <option key={c.id} value={c.id}>
              {c.nombre}
            </option>
          ))}
        </select>

        <label className="block text-xs font-medium text-text-secondary" htmlFor="prof-materia">
          Materia
        </label>
        <select
          id="prof-materia"
          name="prof-materia"
          className="w-full rounded-md border border-border bg-surface-card px-3 py-2 text-sm"
        >
          <option value="">Seleccionar…</option>
          {(materias.data ?? []).map((m) => (
            <option key={m.id} value={m.id}>
              {m.codigo} — {m.nombre}
            </option>
          ))}
        </select>

        <Field label="Comisión" id="prof-comision" placeholder="A" hint="Debe coincidir con el padrón importado." />

        {submitError && <p className="text-xs text-status-danger">{submitError}</p>}
        {feedback && <p className="text-xs text-status-success">{feedback}</p>}

        <button
          type="submit"
          disabled={crearMutation.isPending}
          className="rounded-md bg-ink-900 px-4 py-2 text-sm font-medium text-white hover:bg-ink-700 disabled:opacity-60"
        >
          {crearMutation.isPending ? "Creando…" : "Crear profesor y asignación"}
        </button>
      </form>
    </section>
  );
}

function Field({
  label,
  id,
  type = "text",
  placeholder,
  hint,
}: {
  label: string;
  id: string;
  type?: string;
  placeholder?: string;
  hint?: string;
}) {
  return (
    <div>
      <label className="block text-xs font-medium text-text-secondary" htmlFor={id}>
        {label}
      </label>
      <input
        id={id}
        name={id}
        type={type}
        placeholder={placeholder}
        className="mt-1 w-full rounded-md border border-border bg-surface-card px-3 py-2 text-sm"
        autoComplete="off"
      />
      {hint && <p className="mt-1 text-[11px] text-text-secondary">{hint}</p>}
    </div>
  );
}
