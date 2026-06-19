import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { z } from "zod";

import { AuthShell, authLinkClass } from "@/features/auth/components/AuthShell";
import { resetPasswordRequest } from "@/features/auth/services/authService";
import { Button } from "@/shared/components/ui/Button";
import { Input } from "@/shared/components/ui/Input";

const schema = z
  .object({
    new_password: z.string().min(8, "Mínimo 8 caracteres"),
    confirm_password: z.string().min(8, "Confirmá la contraseña"),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: "Las contraseñas no coinciden",
    path: ["confirm_password"],
  });

type FormValues = z.infer<typeof schema>;

export function ResetPasswordPage() {
  const [params] = useSearchParams();
  const token = params.get("token") ?? "";
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = handleSubmit(async ({ new_password }) => {
    if (!token) {
      setError("Token de reset inválido o expirado.");
      return;
    }
    setError(null);
    try {
      await resetPasswordRequest({ token, new_password });
      navigate("/login");
    } catch {
      setError("No se pudo actualizar la contraseña.");
    }
  });

  return (
    <AuthShell title="Nueva contraseña" subtitle="Elegí una contraseña segura de al menos 8 caracteres.">
      <form className="space-y-4" onSubmit={onSubmit}>
        <Input
          label="Nueva contraseña"
          id="new_password"
          type="password"
          autoComplete="new-password"
          error={errors.new_password?.message}
          {...register("new_password")}
        />
        <Input
          label="Confirmar contraseña"
          id="confirm_password"
          type="password"
          autoComplete="new-password"
          error={errors.confirm_password?.message}
          {...register("confirm_password")}
        />
        {error && (
          <p className="text-sm text-status-danger" role="alert">
            {error}
          </p>
        )}
        <Button type="submit" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? "Guardando…" : "Guardar contraseña"}
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
