import type { ReactNode } from "react";

import { cn } from "@/shared/lib/utils";

type AuthShellProps = {
  children: ReactNode;
  title: string;
  subtitle?: string;
};

export function AuthShell({ children, title, subtitle }: AuthShellProps) {
  return (
    <div className="flex min-h-screen bg-surface">
      <AuthBrandAside className="hidden min-h-screen w-[min(42%,28rem)] shrink-0 md:flex" />

      <main className="flex min-h-screen flex-1 flex-col">
        <AuthBrandMobile />

        <div className="flex flex-1 items-center justify-center px-4 py-8 sm:px-6">
          <div className="w-full max-w-md animate-fade-in">
            <div className="overflow-hidden rounded-lg border border-border bg-surface-card shadow-sm">
              <div className="h-1 bg-accent-gold" aria-hidden />
              <div className="p-6 sm:p-8">
                <div className="mb-6 border-b border-border pb-5">
                  <h1 className="font-display text-2xl font-semibold uppercase tracking-wide text-text-primary">
                    {title}
                  </h1>
                  {subtitle && (
                    <p className="mt-1.5 text-sm text-text-secondary">{subtitle}</p>
                  )}
                </div>
                {children}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function AuthBrandAside({ className }: { className?: string }) {
  return (
    <aside
      className={cn(
        "relative flex flex-col justify-between bg-ink-900 p-10 text-white xl:p-14",
        className,
      )}
    >
      <span className="trace-bar top-8 bottom-8 left-6" aria-hidden />
      <AuthBrandContent />
      <p className="text-xs text-slate-500">© activia-trace · cada acción audita</p>
    </aside>
  );
}

function AuthBrandMobile() {
  return (
    <header className="border-b border-white/10 bg-ink-900 px-4 py-5 text-white md:hidden">
      <div className="relative mx-auto max-w-md pl-3">
        <span className="trace-bar top-0 bottom-0" aria-hidden />
        <p className="font-display text-xl font-semibold uppercase tracking-wide">
          Active <span className="text-accent-gold">Trace</span>
        </p>
        <p className="mt-1 text-xs text-slate-400">Gestión académica multi-tenant</p>
      </div>
    </header>
  );
}

function AuthBrandContent() {
  return (
    <div className="relative max-w-sm space-y-6 pl-3">
      <span className="trace-bar top-0 bottom-0" aria-hidden />
      <p className="font-display text-3xl font-semibold uppercase tracking-wide xl:text-4xl">
        Active <span className="text-accent-gold">Trace</span>
      </p>
      <p className="text-sm leading-relaxed text-slate-300">
        Gestión académica y trazabilidad multi-tenant. Calificaciones, comunicación, equipos
        y auditoría en un solo lugar.
      </p>
      <ul className="space-y-3 text-sm text-slate-400">
        <BrandBullet>Atrasos y entregas por comisión</BrandBullet>
        <BrandBullet>Coordinación docente y liquidaciones</BrandBullet>
        <BrandBullet>Trazabilidad completa por tenant</BrandBullet>
      </ul>
    </div>
  );
}

function BrandBullet({ children }: { children: ReactNode }) {
  return (
    <li className="flex items-start gap-2">
      <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent-gold" aria-hidden />
      {children}
    </li>
  );
}

export const authLinkClass =
  "font-medium text-ink-700 underline underline-offset-4 hover:text-ink-900";
