import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import { z } from "zod";

import { forgotPasswordRequest } from "@/features/auth/services/authService";

const schema = z.object({
  tenant_slug: z.string().min(1),
  email: z.string().email(),
});

type FormValues = z.infer<typeof schema>;

export function ForgotPasswordPage() {
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

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
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        <h1 className="text-xl font-semibold">Recuperar contraseña</h1>
        {sent ? (
          <p className="mt-4 text-sm text-slate-600">
            Si la cuenta existe, recibirás instrucciones por email.
          </p>
        ) : (
          <form className="mt-6 space-y-4" onSubmit={onSubmit}>
            <input
              placeholder="Tenant"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              {...register("tenant_slug")}
            />
            <input
              type="email"
              placeholder="Email"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              {...register("email")}
            />
            {error && <p className="text-sm text-red-600">{error}</p>}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full rounded-lg bg-slate-900 px-4 py-2 text-sm text-white"
            >
              Enviar
            </button>
          </form>
        )}
        <p className="mt-4 text-center text-sm">
          <Link to="/login" className="underline">
            Volver al login
          </Link>
        </p>
      </div>
    </div>
  );
}
