import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { z } from "zod";

import { useAuth } from "@/features/auth/hooks/AuthProvider";

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
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        <h1 className="text-xl font-semibold">Verificación 2FA</h1>
        <p className="mt-1 text-sm text-slate-600">Ingresá el código de tu autenticador</p>
        <form className="mt-6 space-y-4" onSubmit={onSubmit}>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="code">
              Código
            </label>
            <input
              id="code"
              inputMode="numeric"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
              {...register("code")}
            />
            {errors.code && <p className="mt-1 text-xs text-red-600">{errors.code.message}</p>}
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white"
          >
            Verificar
          </button>
        </form>
      </div>
    </div>
  );
}
