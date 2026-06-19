import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import { z } from "zod";

import { AuthShell, authLinkClass } from "@/features/auth/components/AuthShell";
import { forgotPasswordRequest } from "@/features/auth/services/authService";
import { Button } from "@/shared/components/ui/Button";
import { Input } from "@/shared/components/ui/Input";

const schema = z.object({
  tenant_slug: z.string().min(1, "Ingresá el código de institución"),
  email: z.string().email("Email inválido"),
});

type FormValues = z.infer<typeof schema>;

export function ForgotPasswordPage() {
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { tenant_slug: import.meta.env.DEV ? "demo" : "" },
  });

  const onSubmit = handleSubmit(async (values) => {
    setError(null);
    try {
      await forgotPasswordRequest(values);
      setSent(true);
    } catch {
      setError("No se pudo procesar la solicitud");
    }
  });

  return (
    <AuthShell
      title="Recuperar contraseña"
      subtitle="Te enviaremos instrucciones si la cuenta existe."
    >
      {sent ? (
        <p className="text-sm text-text-secondary">
          Si la cuenta existe, recibirás instrucciones por email en los próximos minutos.
        </p>
      ) : (
        <form className="space-y-4" onSubmit={onSubmit}>
          <Input
            label="Código de institución"
            id="forgot-tenant"
            placeholder="demo"
            error={errors.tenant_slug?.message}
            {...register("tenant_slug")}
          />
          <Input
            label="Correo electrónico"
            id="forgot-email"
            type="email"
            placeholder="tu@instituto.edu"
            error={errors.email?.message}
            {...register("email")}
          />
          {error && (
            <p className="text-sm text-status-danger" role="alert">
              {error}
            </p>
          )}
          <Button type="submit" className="w-full" disabled={isSubmitting}>
            {isSubmitting ? "Enviando…" : "Enviar instrucciones"}
          </Button>
        </form>
      )}

      <p className="mt-5 text-center text-sm">
        <Link className={authLinkClass} to="/login">
          Volver al login
        </Link>
      </p>
    </AuthShell>
  );
}
