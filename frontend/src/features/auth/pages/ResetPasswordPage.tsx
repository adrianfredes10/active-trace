import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { z } from "zod";

import { resetPasswordRequest } from "@/features/auth/services/authService";

const schema = z
  .object({
    new_password: z.string().min(8, "Mínimo 8 caracteres"),
    confirm_password: z.string().min(8),
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
      setError("Token de reset inválido");
      return;
    }
    setError(null);
    try {
      await resetPasswordRequest({ token, new_password });
      navigate("/login");
    } catch {
      setError("No se pudo actualizar la contraseña");
    }
  });

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        <h1 className="text-xl font-semibold">Nueva contraseña</h1>
        <form className="mt-6 space-y-4" onSubmit={onSubmit}>
          <input
            type="password"
            placeholder="Nueva contraseña"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            {...register("new_password")}
          />
          {errors.new_password && (
            <p className="text-xs text-red-600">{errors.new_password.message}</p>
          )}
          <input
            type="password"
            placeholder="Confirmar"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            {...register("confirm_password")}
          />
          {errors.confirm_password && (
            <p className="text-xs text-red-600">{errors.confirm_password.message}</p>
          )}
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-lg bg-slate-900 px-4 py-2 text-sm text-white"
          >
            Guardar
          </button>
        </form>
        <p className="mt-4 text-center text-sm">
          <Link to="/login" className="underline">
            Volver al login
          </Link>
        </p>
      </div>
    </div>
  );
}
