import { NavLink, Outlet } from "react-router-dom";

import { usePermissions } from "@/features/auth/hooks/usePermissions";

export type SubNavTab = {
  to: string;
  label: string;
  end?: boolean;
  permission: string | null;
  anyOf?: readonly string[];
};

type SubNavLayoutProps = {
  tabs: readonly SubNavTab[];
  ariaLabel: string;
  deniedMessage: string;
};

export function SubNavLayout({ tabs, ariaLabel, deniedMessage }: SubNavLayoutProps) {
  const { hasPermission, isLoading } = usePermissions();

  const visibleTabs = tabs.filter((tab) => {
    if (tab.anyOf?.length) {
      return tab.anyOf.some((p) => hasPermission(p));
    }
    return tab.permission === null || hasPermission(tab.permission);
  });

  if (isLoading) {
    return <p className="text-sm text-text-secondary">Cargando permisos…</p>;
  }

  if (visibleTabs.length === 0) {
    return (
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
        <p className="text-sm text-amber-900">{deniedMessage}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <nav
        className="-mx-1 flex gap-1 overflow-x-auto border-b border-border pb-2"
        aria-label={ariaLabel}
      >
        {visibleTabs.map((tab) => (
          <NavLink
            key={tab.to}
            to={tab.to}
            end={tab.end}
            className={({ isActive }) =>
              `focus-ring shrink-0 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? "bg-ink-900 text-white"
                  : "text-text-secondary hover:bg-surface-card hover:text-text-primary"
              }`
            }
          >
            {tab.label}
          </NavLink>
        ))}
      </nav>
      <Outlet />
    </div>
  );
}
