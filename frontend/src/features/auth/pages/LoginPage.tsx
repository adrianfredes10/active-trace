import { zodResolver } from "@hookform/resolvers/zod";
import axios from "axios";
import { useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { z } from "zod";

import { AuthShell, authLinkClass } from "@/features/auth/components/AuthShell";
import { useAuth } from "@/features/auth/hooks/AuthProvider";
import { Button } from "@/shared/components/ui/Button";
import { Input } from "@/shared/components/ui/Input";
import { cn } from "@/shared/lib/utils";

const DEV_TENANT = "demo";
const DEV_EMAIL = "admin@demo.local";
const DEV_PASSWORD = "Admin1234!";

const DEV_ACCOUNTS = [
  { label: "Admin", email: DEV_EMAIL, password: DEV_PASSWORD },
  { label: "Prof. A", email: "prof-a@demo.local", password: "Prof1234!" },
  { label: "Prof. B", email: "prof-b@demo.local", password: "Prof1234!" },
  { label: "Coord.", email: "coord@demo.local", password: "Coord1234!" },
  { label: "Finanzas", email: "finanzas@demo.local", password: "Fin1234!" },
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
  const loginInFlight = useRef(false);
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
    if (loginInFlight.current) {
      return;
    }
    loginInFlight.current = true;
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
        setError("Demasiados intentos fallidos. Esperá 1 minuto y probá de nuevo.");
        return;
      }
      setError("Email o contraseña incorrectos.");
    } finally {
      loginInFlight.current = false;
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
    await completeLogin({ tenant_slug: DEV_TENANT, email, password });
    setDevLoadingEmail(null);
  };

  return (
    <AuthShell title="Iniciar sesión" subtitle="Ingresá con tu cuenta institucional.">
      {import.meta.env.DEV && (
        <section
          className="mb-6 rounded-md border border-border bg-surface p-4"
          aria-label="Acceso demo rápido"
        >
          <p className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-text-secondary">
            <span className="h-1.5 w-1.5 rounded-full bg-accent-gold" aria-hidden />
            Acceso demo rápido
          </p>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
            {DEV_ACCOUNTS.map((acc) => (
              <button
                key={acc.email}
                type="button"
                disabled={devLoadingEmail !== null || isSubmitting}
                onClick={() => void onDevLogin(acc.email, acc.password)}
                className={cn(
                  "focus-ring rounded-md border border-border bg-surface-card px-2.5 py-2 text-left transition-colors",
                  "hover:border-accent-gold/40 hover:bg-surface disabled:opacity-50",
                )}
              >
                <span className="block text-xs font-semibold text-text-primary">
                  {devLoadingEmail === acc.email ? "Entrando…" : acc.label}
                </span>
                <span className="mt-0.5 block truncate font-mono text-[10px] text-text-secondary">
                  {acc.email}
                </span>
              </button>
            ))}
          </div>
        </section>
      )}

      <form className="space-y-4" onSubmit={onSubmit}>
        {!import.meta.env.DEV && (
          <Input
            label="Código de institución"
            id="tenant_slug"
            placeholder="ej: demo, utn-frba"
            autoComplete="organization"
            error={errors.tenant_slug?.message}
            {...register("tenant_slug")}
          />
        )}

        <Input
          label="Correo electrónico"
          id="email"
          type="email"
          placeholder="admin@demo.local"
          autoComplete="username"
          error={errors.email?.message}
          {...register("email")}
        />

        <Input
          label="Contraseña"
          id="password"
          type="password"
          placeholder="••••••••"
          autoComplete="current-password"
          error={errors.password?.message}
          {...register("password")}
        />

        {error && (
          <p className="text-sm text-status-danger" role="alert">
            {error}
          </p>
        )}

        <Button type="submit" className="w-full" disabled={isSubmitting || devLoadingEmail !== null}>
          {isSubmitting ? "Ingresando…" : "Ingresar a mi cuenta"}
        </Button>
      </form>

      <p className="mt-5 text-center text-sm">
        <Link className={authLinkClass} to="/forgot-password">
          ¿Olvidaste tu contraseña?
        </Link>
      </p>
    </AuthShell>
  );
}
