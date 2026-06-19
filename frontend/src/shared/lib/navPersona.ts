export type UserPersona = "ADMIN" | "FINANZAS" | "COORDINADOR" | "PROFESOR" | "TUTOR" | "OTHER";

const PERSONA_ORDER: UserPersona[] = [
  "ADMIN",
  "FINANZAS",
  "COORDINADOR",
  "PROFESOR",
  "TUTOR",
];

const PERSONA_PREFIXES: Record<UserPersona, readonly string[]> = {
  ADMIN: ["/", "/admin", "/auditoria"],
  FINANZAS: ["/", "/finanzas"],
  COORDINADOR: ["/", "/coordinacion", "/coloquios"],
  PROFESOR: ["/", "/comision", "/encuentros"],
  TUTOR: ["/", "/comision", "/encuentros"],
  OTHER: ["/"],
};

export function resolvePersona(
  roles: readonly string[],
  permissions: readonly string[] = [],
): UserPersona {
  for (const persona of PERSONA_ORDER) {
    if (roles.includes(persona)) return persona;
  }
  if (permissions.includes("estructura:gestionar") || permissions.includes("usuarios:gestionar")) {
    return "ADMIN";
  }
  if (permissions.includes("liquidaciones:grilla") || permissions.includes("facturas:gestionar")) {
    return "FINANZAS";
  }
  if (permissions.includes("equipos:asignar")) {
    return "COORDINADOR";
  }
  if (permissions.includes("atrasados:ver") || permissions.includes("encuentros:gestionar")) {
    return "PROFESOR";
  }
  return "OTHER";
}

export function isPathAllowedForPersona(pathname: string, persona: UserPersona): boolean {
  return PERSONA_PREFIXES[persona].some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
  );
}

export function isNavPathAllowedForPersona(path: string, persona: UserPersona): boolean {
  if (path === "/") return true;
  return PERSONA_PREFIXES[persona].some(
    (prefix) => prefix !== "/" && (path === prefix || path.startsWith(`${prefix}/`)),
  );
}
