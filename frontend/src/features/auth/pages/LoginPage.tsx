import { zodResolver } from "@hookform/resolvers/zod";
import axios from "axios";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { z } from "zod";

import { useAuth } from "@/features/auth/hooks/AuthProvider";

const DEV_TENANT = "demo";
const DEV_EMAIL = "admin@demo.local";
const DEV_PASSWORD = "Admin1234!";

const schema = z.object({
  tenant_slug: z
    .string()
    .min(1, "Ingresá el código de institución")
    .transform((v) => v.trim().toLowerCase())
    .pipe(z.string().min(1, "Ingresá el código de institución")),
  email: z
    .string()
    .email("Email inválido")
    .transform((v) => v.trim().toLowerCase()),
  password: z.string().min(1, "Ingresá la contraseña"),
});

type FormValues = z.infer<typeof schema>;

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [devLoading, setDevLoading] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      tenant_slug: DEV_TENANT,
      email: DEV_EMAIL,
      password: DEV_PASSWORD,
    },
  });

  const completeLogin = async (payload: {
    tenant_slug: string;
    email: string;
    password: string;
  }) => {
    setError(null);
    try {
      const result = await login(payload);
      if (result.requires2fa && result.challengeToken) {
        navigate("/2fa", { state: { challengeToken: result.challengeToken } });
        return;
      }
      navigate("/");
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 429) {
        setError("Demasiados intentos. Esperá 1 minuto y probá de nuevo.");
        return;
      }
      setError("Email o contraseña incorrectos.");
    }
  };

  const onSubmit = handleSubmit((values) =>
    completeLogin({
      ...values,
      tenant_slug: import.meta.env.DEV ? DEV_TENANT : values.tenant_slug,
    }),
  );

  const onDevLogin = async () => {
    setDevLoading(true);
    await completeLogin({
      tenant_slug: DEV_TENANT,
      email: DEV_EMAIL,
      password: DEV_PASSWORD,
    });
    setDevLoading(false);
  };

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">activia-trace</h1>
        <p className="mt-1 text-sm text-slate-600">Iniciá sesión en tu institución</p>

        {import.meta.env.DEV && (
          <div className="mt-4 space-y-2">
            <button
              type="button"
              disabled={devLoading || isSubmitting}
              onClick={() => void onDevLogin()}
              className="w-full rounded-lg bg-emerald-600 px-4 py-3 text-sm font-semibold text-white hover:bg-emerald-500 disabled:opacity-60"
            >
              {devLoading ? "Entrando…" : "Entrar al demo (1 clic)"}
            </button>
            <p className="text-center text-xs text-slate-500">
              Instituto Demo · admin@demo.local
            </p>
          </div>
        )}

        <form className="mt-6 space-y-4" onSubmit={onSubmit}>
          {!import.meta.env.DEV && (
            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="tenant_slug">
                Institución
              </label>
              <input
                id="tenant_slug"
                placeholder="ej: demo, utn-frba"
                autoComplete="organization"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
                {...register("tenant_slug")}
              />
              <p className="mt-1 text-xs text-slate-500">
                Código corto de tu facultad o instituto (te lo da el admin).
              </p>
              {errors.tenant_slug && (
                <p className="mt-1 text-xs text-red-600">{errors.tenant_slug.message}</p>
              )}
            </div>
          )}

          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="email">
              Email
            </label>
            <input
              id="email"
              type="email"
              placeholder="admin@demo.local"
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
              placeholder="Admin1234!"
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
            disabled={isSubmitting || devLoading}
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
