import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import { useAuth } from "@/features/auth/hooks/AuthProvider";
import { usePermissions } from "@/features/auth/hooks/usePermissions";

function getInitials(email: string): string {
  const local = email.split("@")[0] ?? email;
  const parts = local.split(/[._-]/).filter(Boolean);
  if (parts.length >= 2) {
    return `${parts[0]![0] ?? ""}${parts[1]![0] ?? ""}`.toUpperCase();
  }
  return local.slice(0, 2).toUpperCase();
}

function inferRoleLabel(permissions: string[]): string {
  if (permissions.includes("estructura:gestionar") || permissions.includes("usuarios:gestionar")) {
    return "Administrador";
  }
  if (permissions.includes("liquidaciones:grilla")) {
    return "Finanzas";
  }
  if (permissions.includes("equipos:asignar")) {
    return "Coordinador";
  }
  if (permissions.includes("atrasados:ver")) {
    return "Profesor";
  }
  if (permissions.includes("auditoria:ver")) {
    return "Auditoría";
  }
  return "Usuario";
}

type UserMenuProps = {
  tenant?: string;
};

export function UserMenu({ tenant = "demo" }: UserMenuProps) {
  const { logout, user } = useAuth();
  const { permissions } = usePermissions();
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  const close = useCallback(() => setOpen(false), []);

  useEffect(() => {
    if (!open) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        close();
      }
    };

    const onPointerDown = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        close();
      }
    };

    document.addEventListener("keydown", onKeyDown);
    document.addEventListener("mousedown", onPointerDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.removeEventListener("mousedown", onPointerDown);
    };
  }, [open, close]);

  if (!user?.email) {
    return null;
  }

  const roleLabel = inferRoleLabel(permissions);

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        aria-expanded={open}
        aria-haspopup="menu"
        onClick={() => setOpen((value) => !value)}
        className="focus-ring flex items-center gap-2 rounded-md px-1 py-1"
      >
        <span className="hidden text-right sm:block">
          <span className="block max-w-[140px] truncate text-xs font-medium text-text-primary">
            {tenant}
          </span>
        </span>
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-ink-900 text-xs font-semibold text-white">
          {getInitials(user.email)}
        </span>
        <svg
          className={`h-3.5 w-3.5 text-text-secondary transition-transform ${open ? "rotate-180" : ""}`}
          viewBox="0 0 20 20"
          fill="currentColor"
          aria-hidden
        >
          <path
            fillRule="evenodd"
            d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.94a.75.75 0 111.08 1.04l-4.24 4.5a.75.75 0 01-1.08 0l-4.24-4.5a.75.75 0 01.02-1.06z"
            clipRule="evenodd"
          />
        </svg>
      </button>

      {open && (
        <div
          role="menu"
          className="absolute right-0 z-50 mt-2 w-56 rounded-md border border-border bg-surface-card py-1 shadow-sm animate-fade-in"
        >
          <div className="border-b border-border px-3 py-2.5">
            <p className="truncate text-sm font-medium text-text-primary">{user.email}</p>
            <p className="mt-0.5 text-xs text-text-secondary">
              {tenant} · {roleLabel}
            </p>
          </div>
          <Link
            to="/"
            role="menuitem"
            onClick={close}
            className="focus-ring block px-3 py-2 text-sm text-text-primary hover:bg-surface"
          >
            Mi perfil
          </Link>
          <Link
            to="/2fa"
            role="menuitem"
            onClick={close}
            className="focus-ring block px-3 py-2 text-sm text-text-primary hover:bg-surface"
          >
            Seguridad (2FA)
          </Link>
          <div className="my-1 border-t border-border" />
          <button
            type="button"
            role="menuitem"
            onClick={() => {
              close();
              void logout();
            }}
            className="focus-ring block w-full px-3 py-2 text-left text-sm text-status-danger hover:bg-surface"
          >
            Cerrar sesión
          </button>
        </div>
      )}
    </div>
  );
}
