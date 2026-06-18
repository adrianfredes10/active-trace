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

const DEV_ACCOUNTS = [
  { label: "Admin", email: DEV_EMAIL, password: DEV_PASSWORD, accent: "bg-emerald-600 hover:bg-emerald-500" },
  { label: "Prof. A", email: "prof-a@demo.local", password: "Prof1234!", accent: "bg-slate-700 hover:bg-slate-600" },
  { label: "Prof. B", email: "prof-b@demo.local", password: "Prof1234!", accent: "bg-slate-700 hover:bg-slate-600" },
  { label: "Coord.", email: "coord@demo.local", password: "Coord1234!", accent: "bg-slate-700 hover:bg-slate-600" },
  { label: "Finanzas", email: "finanzas@demo.local", password: "Fin1234!", accent: "bg-slate-700 hover:bg-slate-600" },
] as const;

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
  const [devLoadingEmail, setDevLoadingEmail] = useState<string | null>(null);
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

  const onDevLogin = async (email: string, password: string) => {
    setDevLoadingEmail(email);
    await completeLogin({
      tenant_slug: DEV_TENANT,
      email,
      password,
    });
    setDevLoadingEmail(null);
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-slate-950 px-4 py-12 overflow-hidden font-sans">
      {/* Background Gradients & Effects */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.015)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.015)_1px,transparent_1px)] bg-[size:30px_30px] pointer-events-none" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[550px] h-[550px] bg-indigo-500/10 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute top-1/4 left-1/4 w-[350px] h-[350px] bg-violet-600/5 rounded-full blur-[80px] pointer-events-none" />

      <div className="relative w-full max-w-md rounded-2xl border border-white/10 bg-slate-900/75 p-8 shadow-2xl backdrop-blur-xl animate-fade-in">
        <div className="flex flex-col items-center text-center mb-6">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-500/10 border border-indigo-500/25 text-indigo-400 mb-4 shadow-inner">
            <svg className="h-7 w-7 text-indigo-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="5" r="3" className="fill-indigo-950" />
              <circle cx="5" cy="19" r="3" className="fill-indigo-950" />
              <circle cx="19" cy="19" r="3" className="fill-indigo-950" />
              <path d="M5 16V9.5a2.5 2.5 0 0 1 5 0V14.5a2.5 2.5 0 0 0 5 0V8" />
            </svg>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-white via-indigo-100 to-indigo-200 bg-clip-text text-transparent">
            activia-trace
          </h1>
          <p className="mt-1.5 text-xs text-slate-400 tracking-wide">
            Gestión Académica y Trazabilidad Multi-tenant
          </p>
        </div>

        {import.meta.env.DEV && (
          <div className="mt-5 rounded-xl border border-slate-800/80 bg-slate-950/40 p-4">
            <p className="text-[10px] font-bold uppercase tracking-wider text-indigo-400 mb-3 flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-indigo-500 animate-pulse" />
              Acceso Demo Rápido
            </p>
            <div className="grid grid-cols-2 gap-2">
              {DEV_ACCOUNTS.map((acc) => (
                <button
                  key={acc.email}
                  type="button"
                  disabled={devLoadingEmail !== null || isSubmitting}
                  onClick={() => void onDevLogin(acc.email, acc.password)}
                  className="group flex flex-col items-start rounded-lg border border-slate-800/80 bg-slate-900/40 p-2.5 text-left transition-all duration-150 hover:border-indigo-500/50 hover:bg-slate-900 disabled:opacity-50 cursor-pointer"
                >
                  <span className="text-xs font-bold text-slate-200 group-hover:text-indigo-300 transition-colors">
                    {devLoadingEmail === acc.email ? "Entrando…" : acc.label}
                  </span>
                  <span className="text-[9px] text-slate-500 truncate w-full mt-0.5">
                    {acc.email}
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}

        <form className="mt-6 space-y-4" onSubmit={onSubmit}>
          {!import.meta.env.DEV && (
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1.5" htmlFor="tenant_slug">
                Código de Institución
              </label>
              <input
                id="tenant_slug"
                placeholder="ej: demo, utn-frba"
                autoComplete="organization"
                className="w-full rounded-xl border border-slate-800 bg-slate-950/60 px-4 py-2.5 text-sm text-slate-200 outline-none placeholder-slate-600 transition-all duration-200 focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10"
                {...register("tenant_slug")}
              />
              <p className="mt-1 text-[10px] text-slate-500">
                Código corto asignado a tu facultad o institución.
              </p>
              {errors.tenant_slug && (
                <p className="mt-1 text-xs text-red-500">{errors.tenant_slug.message}</p>
              )}
            </div>
          )}

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1.5" htmlFor="email">
              Correo Electrónico
            </label>
            <input
              id="email"
              type="email"
              placeholder="admin@demo.local"
              autoComplete="username"
              className="w-full rounded-xl border border-slate-800 bg-slate-950/60 px-4 py-2.5 text-sm text-slate-200 outline-none placeholder-slate-700 transition-all duration-200 focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10"
              {...register("email")}
            />
            {errors.email && (
              <p className="mt-1 text-xs text-red-500">{errors.email.message}</p>
            )}
          </div>
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1.5" htmlFor="password">
              Contraseña
            </label>
            <input
              id="password"
              type="password"
              placeholder="••••••••"
              autoComplete="current-password"
              className="w-full rounded-xl border border-slate-800 bg-slate-950/60 px-4 py-2.5 text-sm text-slate-200 outline-none placeholder-slate-700 transition-all duration-200 focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10"
              {...register("password")}
            />
            {errors.password && (
              <p className="mt-1 text-xs text-red-500">{errors.password.message}</p>
            )}
          </div>
          {error && <p className="text-sm text-red-500 font-medium">{error}</p>}
          <button
            type="submit"
            disabled={isSubmitting || devLoadingEmail !== null}
            className="w-full rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-600/20 hover:bg-indigo-500 hover:shadow-indigo-600/35 transition-all duration-150 disabled:opacity-60 cursor-pointer"
          >
            {isSubmitting ? "Ingresando…" : "Ingresar a mi cuenta"}
          </button>
        </form>

        <p className="mt-5 text-center text-xs">
          <Link className="text-indigo-400 hover:text-indigo-300 transition-colors font-medium underline underline-offset-4" to="/forgot-password">
            ¿Olvidaste tu contraseña?
          </Link>
        </p>
      </div>
    </div>
  );
}
