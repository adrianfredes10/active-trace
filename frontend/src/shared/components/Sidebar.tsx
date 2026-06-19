import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";

import { usePermissions } from "@/features/auth/hooks/usePermissions";

import { filterVisibleGroups, NAV_GROUPS, type NavGroup } from "./navConfig";

const SIDEBAR_COLLAPSED_KEY = "activia.sidebar.collapsed";
const ACCORDION_KEY = "activia.sidebar.accordion";

type SidebarProps = {
  collapsed: boolean;
  onCollapsedChange: (collapsed: boolean) => void;
  mobileOpen: boolean;
  onMobileClose: () => void;
};

function NavIcon({ name }: { name: string }) {
  const common = "h-4 w-4 shrink-0";
  switch (name) {
    case "Inicio":
      return (
        <svg className={common} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M3 10.5L12 3l9 7.5V20a1 1 0 01-1 1h-5v-6H9v6H4a1 1 0 01-1-1v-9.5z" />
        </svg>
      );
    case "Mi comisión":
      return (
        <svg className={common} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M4 6h16M4 12h16M4 18h10" />
        </svg>
      );
    case "Coordinación":
      return (
        <svg className={common} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="9" cy="7" r="3" />
          <circle cx="17" cy="7" r="3" />
          <path d="M3 20c0-3 3-5 6-5s6 2 6 5M13 20c0-2 2-4 4-4" />
        </svg>
      );
    case "Crear encuentro":
    case "Encuentros":
      return (
        <svg className={common} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="3" y="4" width="18" height="18" rx="2" />
          <path d="M16 2v4M8 2v4M3 10h18" />
        </svg>
      );
    case "Coloquios":
      return (
        <svg className={common} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M9 11l3 3L22 4" />
          <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" />
        </svg>
      );
    case "Liquidaciones":
    case "Facturas":
      return (
        <svg className={common} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 2v20M17 5H9.5a3.5 3.5 0 000 7H14a3.5 3.5 0 010 7H6" />
        </svg>
      );
    case "Panel":
      return (
        <svg className={common} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="3" y="3" width="7" height="7" rx="1" />
          <rect x="14" y="3" width="7" height="7" rx="1" />
          <rect x="3" y="14" width="7" height="7" rx="1" />
          <rect x="14" y="14" width="7" height="7" rx="1" />
        </svg>
      );
    case "Carreras":
    case "Materias":
    case "Cohortes":
      return (
        <svg className={common} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M4 19.5A2.5 2.5 0 016.5 17H20" />
          <path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z" />
        </svg>
      );
    case "Usuarios":
      return (
        <svg className={common} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="9" cy="7" r="3" />
          <path d="M3 20c0-3 3-5 6-5s6 2 6 5M16 11h6M19 8v6" />
        </svg>
      );
    case "Admin":
      return (
        <svg className={common} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 15.5a3.5 3.5 0 100-7 3.5 3.5 0 000 7z" />
          <path d="M19.4 15a1.7 1.7 0 00.3 1.9l.1.1a2 2 0 01-2.8 2.8l-.1-.1a1.7 1.7 0 00-1.9-.3 1.7 1.7 0 00-1 1.5V21a2 2 0 01-4 0v-.2a1.7 1.7 0 00-1-1.5 1.7 1.7 0 00-1.9.3l-.1.1a2 2 0 01-2.8-2.8l.1-.1a1.7 1.7 0 00.3-1.9 1.7 1.7 0 00-1.5-1H3a2 2 0 010-4h.2a1.7 1.7 0 001.5-1 1.7 1.7 0 00-.3-1.9l-.1-.1a2 2 0 012.8-2.8l.1.1a1.7 1.7 0 001.9.3H9a1.7 1.7 0 001-1.5V3a2 2 0 014 0v.2a1.7 1.7 0 001 1.5 1.7 1.7 0 001.9-.3l.1-.1a2 2 0 012.8 2.8l-.1.1a1.7 1.7 0 00-.3 1.9 1.7 1.7 0 001.5 1H21a2 2 0 010 4h-.2a1.7 1.7 0 00-1.5 1z" />
        </svg>
      );
    case "Auditoría":
      return (
        <svg className={common} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2" />
          <rect x="9" y="3" width="6" height="4" rx="1" />
          <path d="M9 12h6M9 16h6" />
        </svg>
      );
    default:
      return <span className={`${common} rounded-full bg-current opacity-40`} />;
  }
}

function SidebarNav({
  groups,
  collapsed,
  openSections,
  onToggleSection,
  onNavigate,
}: {
  groups: NavGroup[];
  collapsed: boolean;
  openSections: Record<string, boolean>;
  onToggleSection: (id: string) => void;
  onNavigate?: () => void;
}) {
  return (
    <nav className="flex-1 space-y-1 overflow-y-auto px-2 py-3">
      {groups.map((group) => {
        const isStandalone = group.label === null;

        if (isStandalone) {
          return group.items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              onClick={onNavigate}
              title={collapsed ? item.label : undefined}
              className={({ isActive }) =>
                `focus-ring group relative flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors ${
                  isActive
                    ? "bg-ink-700 text-white"
                    : "text-slate-300 hover:bg-ink-700/70 hover:text-white"
                } ${collapsed ? "justify-center px-2" : ""}`
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <span
                      className="trace-bar top-1 bottom-1"
                      aria-hidden
                    />
                  )}
                  <NavIcon name={item.label} />
                  {!collapsed && <span className="truncate">{item.label}</span>}
                </>
              )}
            </NavLink>
          ));
        }

        const sectionOpen = openSections[group.id] ?? true;
        const hasSingleItem = group.items.length === 1;

        if (collapsed && hasSingleItem) {
          const item = group.items[0]!;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onNavigate}
              title={item.label}
              className={({ isActive }) =>
                `focus-ring group relative flex items-center justify-center rounded-md px-2 py-2 text-sm transition-colors ${
                  isActive
                    ? "bg-ink-700 text-white"
                    : "text-slate-300 hover:bg-ink-700/70 hover:text-white"
                }`
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && <span className="trace-bar top-1 bottom-1" aria-hidden />}
                  <NavIcon name={item.label} />
                </>
              )}
            </NavLink>
          );
        }

        return (
          <div key={group.id} className="pt-1">
            {!collapsed && (
              <button
                type="button"
                onClick={() => onToggleSection(group.id)}
                className="focus-ring flex w-full items-center justify-between rounded-md px-3 py-1.5 text-left text-[11px] font-semibold uppercase tracking-wider text-slate-400 hover:text-slate-200"
              >
                <span>{group.label}</span>
                <svg
                  className={`h-3 w-3 transition-transform ${sectionOpen ? "rotate-180" : ""}`}
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
            )}
            {(collapsed || sectionOpen) &&
              group.items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === "/" || item.to === "/admin"}
                  onClick={onNavigate}
                  title={collapsed ? item.label : undefined}
                  className={({ isActive }) =>
                    `focus-ring group relative flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors ${
                      isActive
                        ? "bg-ink-700 text-white"
                        : "text-slate-300 hover:bg-ink-700/70 hover:text-white"
                    } ${collapsed ? "justify-center px-2" : "ml-0"}`}
                >
                  {({ isActive }) => (
                    <>
                      {isActive && <span className="trace-bar top-1 bottom-1" aria-hidden />}
                      <NavIcon name={item.label} />
                      {!collapsed && <span className="truncate">{item.label}</span>}
                    </>
                  )}
                </NavLink>
              ))}
          </div>
        );
      })}
    </nav>
  );
}

function SidebarPanel({
  collapsed,
  onCollapsedChange,
  onNavigate,
  className = "",
}: {
  collapsed: boolean;
  onCollapsedChange: (collapsed: boolean) => void;
  onNavigate?: () => void;
  className?: string;
}) {
  const { hasPermission, persona } = usePermissions();
  const visibleGroups = filterVisibleGroups(NAV_GROUPS, hasPermission, persona);

  const [openSections, setOpenSections] = useState<Record<string, boolean>>(() => {
    try {
      const stored = localStorage.getItem(ACCORDION_KEY);
      return stored ? (JSON.parse(stored) as Record<string, boolean>) : {};
    } catch {
      return {};
    }
  });

  useEffect(() => {
    localStorage.setItem(ACCORDION_KEY, JSON.stringify(openSections));
  }, [openSections]);

  const toggleSection = (id: string) => {
    setOpenSections((prev) => ({ ...prev, [id]: !(prev[id] ?? true) }));
  };

  return (
    <aside
      className={`flex h-full flex-col bg-ink-900 text-white transition-[width] duration-200 ${
        collapsed ? "w-16" : "w-60"
      } ${className}`}
    >
      <div
        className={`flex h-14 shrink-0 items-center border-b border-white/10 ${
          collapsed ? "justify-center px-2" : "px-4"
        }`}
      >
        {collapsed ? (
          <span className="font-display text-sm font-semibold text-accent-gold" title="Active Trace">
            AT
          </span>
        ) : (
          <span className="font-display text-sm font-semibold uppercase tracking-wide text-white">
            Active <span className="text-accent-gold">Trace</span>
          </span>
        )}
      </div>

      <SidebarNav
        groups={visibleGroups}
        collapsed={collapsed}
        openSections={openSections}
        onToggleSection={toggleSection}
        onNavigate={onNavigate}
      />

      <div className="hidden shrink-0 border-t border-white/10 p-2 md:block">
        <button
          type="button"
          onClick={() => onCollapsedChange(!collapsed)}
          aria-label={collapsed ? "Expandir menú" : "Colapsar menú"}
          className="focus-ring flex w-full items-center justify-center gap-2 rounded-md px-2 py-2 text-xs text-slate-400 hover:bg-ink-700 hover:text-white"
        >
          <svg
            className={`h-4 w-4 transition-transform ${collapsed ? "rotate-180" : ""}`}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M15 18l-6-6 6-6" />
          </svg>
          {!collapsed && <span>Colapsar</span>}
        </button>
      </div>
    </aside>
  );
}

export function Sidebar({ collapsed, onCollapsedChange, mobileOpen, onMobileClose }: SidebarProps) {
  return (
    <>
      <div className="sticky top-0 hidden h-screen shrink-0 md:block">
        <SidebarPanel collapsed={collapsed} onCollapsedChange={onCollapsedChange} />
      </div>

      {mobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <button
            type="button"
            aria-label="Cerrar menú"
            className="absolute inset-0 bg-ink-900/60"
            onClick={onMobileClose}
          />
          <div className="relative h-full w-60 animate-fade-in">
            <SidebarPanel
              collapsed={false}
              onCollapsedChange={onCollapsedChange}
              onNavigate={onMobileClose}
              className="shadow-lg"
            />
          </div>
        </div>
      )}
    </>
  );
}

export function readSidebarCollapsed(): boolean {
  try {
    return localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === "true";
  } catch {
    return false;
  }
}

export function persistSidebarCollapsed(collapsed: boolean): void {
  try {
    localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(collapsed));
  } catch {
    /* ignore quota errors */
  }
}
