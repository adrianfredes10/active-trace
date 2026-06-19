import { useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";

import { persistSidebarCollapsed, readSidebarCollapsed, Sidebar } from "@/shared/components/Sidebar";
import { UserMenu } from "@/shared/components/UserMenu";
import { ROUTE_TITLES } from "@/shared/components/navConfig";

function PageTitle({ pathname }: { pathname: string }) {
  const title = ROUTE_TITLES[pathname] ?? "Active Trace";

  return (
    <div className="relative min-w-0 pl-3">
      <span className="trace-bar top-0 bottom-0" aria-hidden />
      <h1 className="truncate font-display text-2xl font-semibold uppercase tracking-wide text-text-primary">
        {title}
      </h1>
    </div>
  );
}

export function AppLayout() {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(readSidebarCollapsed);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  const handleCollapsedChange = (value: boolean) => {
    setCollapsed(value);
    persistSidebarCollapsed(value);
  };

  return (
    <div className="flex min-h-screen bg-surface">
      <Sidebar
        collapsed={collapsed}
        onCollapsedChange={handleCollapsedChange}
        mobileOpen={mobileOpen}
        onMobileClose={() => setMobileOpen(false)}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-14 shrink-0 items-center gap-3 border-b border-border bg-surface px-4">
          <button
            type="button"
            aria-label="Abrir menú"
            onClick={() => setMobileOpen(true)}
            className="focus-ring rounded-md p-2 text-text-secondary hover:bg-surface-card md:hidden"
          >
            <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>

          <PageTitle pathname={location.pathname} />

          <div className="ml-auto flex shrink-0 items-center gap-2">
            <button
              type="button"
              aria-label="Avisos pendientes"
              className="focus-ring relative rounded-md p-2 text-text-secondary hover:bg-surface-card"
            >
              <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M15 17h5l-1.4-1.4A2 2 0 0118 14.2V11a6 6 0 10-12 0v3.2c0 .5-.2 1-.6 1.4L4 17h5" />
                <path d="M10 20a2 2 0 004 0" />
              </svg>
            </button>
            <UserMenu tenant="demo" />
          </div>
        </header>

        <main className="mx-auto w-full max-w-7xl flex-1 p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
