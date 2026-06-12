import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { z } from "zod";

import { useAuth } from "@/features/auth/hooks/AuthProvider";

const schema = z.object({
  tenant_slug: z.string().min(1, "Ingresá el tenant"),
  email: z.string().email("Email inválido"),
  password: z.string().min(1, "Ingresá la contraseña"),
});

type FormValues = z.infer<typeof schema>;

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = handleSubmit(async (values) => {
    setError(null);
    try {
      const result = await login(values);
      if (result.requires2fa && result.challengeToken) {
        navigate("/2fa", { state: { challengeToken: result.challengeToken } });
        return;
      }
      navigate("/");
    } catch {
      setError("Credenciales inválidas o tenant incorrecto");
    }
  });

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">activia-trace</h1>
        <p className="mt-1 text-sm text-slate-600">Iniciá sesión en tu institución</p>

        <form className="mt-6 space-y-4" onSubmit={onSubmit}>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="tenant_slug">
              Tenant
            </label>
            <input
              id="tenant_slug"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
              {...register("tenant_slug")}
            />
            {errors.tenant_slug && (
              <p className="mt-1 text-xs text-red-600">{errors.tenant_slug.message}</p>
            )}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="email">
              Email
            </label>
            <input
              id="email"
              type="email"
              autoComplete="username"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
              {...register("email")}
            />
            {errors.email && (
              <p className="mt-1 text-xs text-red-600">{errors.email.message}</p>
            )}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="password">
              Contraseña
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
              {...register("password")}
            />
            {errors.password && (
              <p className="mt-1 text-xs text-red-600">{errors.password.message}</p>
            )}
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-60"
          >
            {isSubmitting ? "Ingresando…" : "Ingresar"}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-slate-600">
          <Link className="text-slate-900 underline" to="/forgot-password">
            ¿Olvidaste tu contraseña?
          </Link>
        </p>
      </div>
    </div>
  );
}
