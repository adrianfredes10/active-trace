import { Link } from "react-router-dom";

import { useAuth } from "@/features/auth/hooks/AuthProvider";
import { usePermissions } from "@/features/auth/hooks/usePermissions";

const DEMO_ROLES = [
  {
    label: "Administrador",
    email: "admin@demo.local",
    password: "Admin1234!",
    ruta: "/admin",
    permiso: null as string | null,
    anyOf: ["estructura:gestionar", "usuarios:gestionar"],
    pasos: "Crear carrera, materia y usuario. Revisar estructura del tenant.",
  },
  {
    label: "Profesor",
    email: "prof@demo.local",
    password: "Prof1234!",
    ruta: "/comision",
    permiso: "atrasados:ver",
    anyOf: [] as string[],
    pasos: "Ver atrasados (Pedro y María), reportes, umbral y comunicar.",
  },
  {
    label: "Coordinador",
    email: "coord@demo.local",
    password: "Coord1234!",
    ruta: "/coordinacion",
    permiso: "equipos:asignar",
    anyOf: [] as string[],
    pasos: "Equipos docentes, avisos, tareas internas y monitor.",
  },
  {
    label: "Finanzas",
    email: "finanzas@demo.local",
    password: "Fin1234!",
    ruta: "/finanzas",
    permiso: "liquidaciones:grilla",
    anyOf: [] as string[],
    pasos: "Liquidaciones junio 2026 y grilla salarial.",
  },
] as const;

export function HomePage() {
  const { user } = useAuth();
  const { hasPermission } = usePermissions();

  const visibleModules = [
    { to: "/admin", label: "Administración", show: hasPermission("estructura:gestionar") },
    { to: "/comision", label: "Mi comisión", show: hasPermission("atrasados:ver") },
    { to: "/coordinacion", label: "Coordinación", show: hasPermission("equipos:asignar") },
    { to: "/finanzas", label: "Finanzas", show: hasPermission("liquidaciones:grilla") },
    { to: "/auditoria", label: "Auditoría", show: hasPermission("auditoria:ver") },
  ].filter((m) => m.show);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Panel principal</h1>
        <p className="mt-1 text-sm text-slate-600">
          Hola{user?.email ? `, ${user.email}` : ""}. Instituto Demo — tenant{" "}
          <strong>demo</strong>.
        </p>
      </div>

      {visibleModules.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-lg font-medium text-slate-900">Tus módulos</h2>
          <div className="flex flex-wrap gap-2">
            {visibleModules.map((m) => (
              <Link
                key={m.to}
                to={m.to}
                className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-800 hover:bg-slate-50"
              >
                {m.label} →
              </Link>
            ))}
          </div>
        </section>
      )}

      {import.meta.env.DEV && (
        <section className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="text-lg font-medium text-slate-900">Guión sugerido para el video (~10 min)</h2>
          <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm text-slate-700">
            <li>
              <strong>Login admin</strong> — botón verde o admin@demo.local / Admin1234!
            </li>
            <li>
              <strong>Admin → Estructura</strong> — mostrar TUP y MAT01; crear una carrera o materia de prueba.
            </li>
            <li>
              <strong>Admin → Usuarios</strong> — listar y crear usuario (email con dominio válido, ej. @example.com).
            </li>
            <li>
              <strong>Auditoría</strong> — panel de métricas y log (acciones de padrón y calificaciones).
            </li>
            <li>
              <strong>Salir → Finanzas</strong> — finanzas@demo.local / Fin1234! → liquidaciones 2026-06.
            </li>
            <li>
              <strong>Salir → Profesor</strong> — prof@demo.local → Mi comisión → Atrasados (2 alumnos).
            </li>
            <li>
              <strong>Coordinador</strong> — coord@demo.local → Equipos, Avisos, Tareas.
            </li>
          </ol>

          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            {DEMO_ROLES.map((rol) => (
              <div
                key={rol.email}
                className="rounded-lg border border-slate-100 bg-slate-50 px-4 py-3 text-sm"
              >
                <p className="font-medium text-slate-900">{rol.label}</p>
                <p className="mt-1 font-mono text-xs text-slate-600">
                  {rol.email} / {rol.password}
                </p>
                <p className="mt-2 text-slate-600">{rol.pasos}</p>
                <Link
                  to={rol.ruta}
                  className="mt-2 inline-block text-xs font-medium text-slate-900 underline"
                >
                  Ir a {rol.ruta}
                </Link>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
