import { PermissionGate } from "@/features/auth/components/PermissionGate";

export function HomePage() {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold text-slate-900">Panel principal</h1>
      <p className="text-slate-600">
        Shell autenticado de activia-trace. Las features de dominio se agregan en C-22+.
      </p>
      <PermissionGate permission="auditoria:ver">
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
          Tenés acceso a auditoría — ver menú lateral.
        </div>
      </PermissionGate>
    </div>
  );
}
