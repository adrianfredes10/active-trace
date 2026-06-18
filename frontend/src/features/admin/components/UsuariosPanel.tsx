import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { useState } from "react";

import {
  crearUsuarioAdmin,
  fetchUsuariosAdmin,
} from "@/features/admin/services/usuarioAdminService";

export function UsuariosPanel() {
  const queryClient = useQueryClient();
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["admin-usuarios"],
    queryFn: fetchUsuariosAdmin,
    retry: 1,
  });

  const crearMutation = useMutation({
    mutationFn: crearUsuarioAdmin,
    onSuccess: () => {
      setSubmitError(null);
      setFeedback("Usuario creado correctamente.");
      void queryClient.invalidateQueries({ queryKey: ["admin-usuarios"] });
    },
    onError: (error) => {
      setFeedback(null);
      setSubmitError(formatApiError(error));
    },
  });

  return (
    <div className="space-y-6">
      <section className="max-w-md rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <h3 className="mb-3 text-sm font-semibold text-slate-800">Nuevo usuario</h3>
        <form
          id="form-usuario"
          className="space-y-3"
          onSubmit={(e) => {
            e.preventDefault();
            const form = e.currentTarget;
            const email = (form.elements.namedItem("usuario-email") as HTMLInputElement).value.trim();
            const password = (form.elements.namedItem("usuario-password") as HTMLInputElement).value;
            const nombre = (form.elements.namedItem("usuario-nombre") as HTMLInputElement).value.trim();
            const apellidos = (form.elements.namedItem("usuario-apellidos") as HTMLInputElement).value.trim();
            const legajo = (form.elements.namedItem("usuario-legajo") as HTMLInputElement).value.trim();

            if (!email || password.length < 8) {
              setFeedback(null);
              setSubmitError("Email y contraseña (mín. 8 caracteres) son obligatorios.");
              return;
            }

            setSubmitError(null);
            setFeedback(null);
            crearMutation.mutate({
              email,
              password,
              nombre: nombre || undefined,
              apellidos: apellidos || undefined,
              legajo: legajo || undefined,
            });
            form.reset();
          }}
        >
          <label className="block text-xs font-medium text-slate-600" htmlFor="usuario-email">
            Email
          </label>
          <input
            id="usuario-email"
            name="usuario-email"
            type="email"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            placeholder="profesor@c07.example.com"
            autoComplete="off"
          />

          <label className="block text-xs font-medium text-slate-600" htmlFor="usuario-password">
            Contraseña
          </label>
          <input
            id="usuario-password"
            name="usuario-password"
            type="password"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            placeholder="Mínimo 8 caracteres"
            autoComplete="new-password"
          />

          <label className="block text-xs font-medium text-slate-600" htmlFor="usuario-nombre">
            Nombre
          </label>
          <input
            id="usuario-nombre"
            name="usuario-nombre"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            placeholder="Nombre"
            autoComplete="off"
          />

          <label className="block text-xs font-medium text-slate-600" htmlFor="usuario-apellidos">
            Apellidos
          </label>
          <input
            id="usuario-apellidos"
            name="usuario-apellidos"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            placeholder="Apellidos"
            autoComplete="off"
          />

          <label className="block text-xs font-medium text-slate-600" htmlFor="usuario-legajo">
            Legajo (opcional)
          </label>
          <input
            id="usuario-legajo"
            name="usuario-legajo"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            placeholder="P-001"
            autoComplete="off"
          />

          <button
            type="submit"
            className="mt-1 w-full cursor-pointer rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white hover:bg-slate-800"
          >
            {crearMutation.isPending ? "Creando…" : "Crear usuario"}
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
          <p className="text-xs text-slate-500">
            Usá dominio válido (ej. @example.com). Demo: prof-a@demo.local / prof-b@demo.local — Prof1234!
          </p>
        </form>
      </section>

      {isLoading && <p className="text-sm text-slate-600">Cargando usuarios…</p>}
      {isError && (
        <p className="text-sm text-red-600" role="alert">
          No se pudo cargar usuarios.
        </p>
      )}
      {!isLoading && !isError && (
        <ul className="divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white text-sm">
          {(data ?? []).map((u) => (
            <li key={u.id} className="flex justify-between px-4 py-2">
              <span>
                {u.apellidos ?? "—"}, {u.nombre ?? "—"}
                {u.legajo ? ` (${u.legajo})` : ""}
              </span>
              <span className="text-slate-500">
                {u.estado}
                {u.facturador ? " · Factura" : ""}
              </span>
            </li>
          ))}
          {(data ?? []).length === 0 && (
            <li className="px-4 py-4 text-center text-slate-500">Sin usuarios activos.</li>
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
    if (error.response?.status === 409) {
      return "Ya existe un usuario con ese email.";
    }
  }
  return "No se pudo crear el usuario. Revisá los datos e intentá de nuevo.";
}
