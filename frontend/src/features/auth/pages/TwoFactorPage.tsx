import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { z } from "zod";

import { AuthShell, authLinkClass } from "@/features/auth/components/AuthShell";
import { useAuth } from "@/features/auth/hooks/AuthProvider";
import { Button } from "@/shared/components/ui/Button";
import { Input } from "@/shared/components/ui/Input";

const schema = z.object({
  code: z.string().min(6, "Código inválido").max(10),
});

type FormValues = z.infer<typeof schema>;

export function TwoFactorPage() {
  const { complete2fa } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const challengeToken = (location.state as { challengeToken?: string } | null)?.challengeToken;
  const [error, setError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  if (!challengeToken) {
    return <Navigate to="/login" replace />;
  }

  const onSubmit = handleSubmit(async ({ code }) => {
    setError(null);
    try {
      await complete2fa(challengeToken, code);
      navigate("/");
    } catch {
      setError("Código 2FA inválido");
    }
  });

  return (
    <AuthShell
      title="Verificación 2FA"
      subtitle="Ingresá el código de tu aplicación autenticadora."
    >
      <form className="space-y-4" onSubmit={onSubmit}>
        <Input
          label="Código de verificación"
          id="code"
          inputMode="numeric"
          autoComplete="one-time-code"
          placeholder="000000"
          error={errors.code?.message}
          {...register("code")}
        />
        {error && (
          <p className="text-sm text-status-danger" role="alert">
            {error}
          </p>
        )}
        <Button type="submit" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? "Verificando…" : "Verificar"}
        </Button>
      </form>

      <p className="mt-5 text-center text-sm">
        <Link className={authLinkClass} to="/login">
          Volver al login
        </Link>
      </p>
    </AuthShell>
  );
}
