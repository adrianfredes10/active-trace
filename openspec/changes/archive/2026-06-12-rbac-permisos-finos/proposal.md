# Change: rbac-permisos-finos (C-04)

## Why

C-03 dejó la autenticación lista, pero el claim `roles` del JWT viaja vacío y ningún endpoint declara qué permiso exige. Sin RBAC, o todo es público o todo es 403 — no hay autorización real. C-04 construye el modelo de autorización del dominio: catálogo administrable rol × permiso (`modulo:accion`), resolución de permisos efectivos server-side por request y el guard `require_permission` fail-closed que habilita el resto de los módulos (calificaciones, comunicación, liquidaciones, auditoría…).

## Decisiones acordadas (governance CRÍTICA)

- **Link usuario↔rol mínimo**: C-04 crea `usuario_rol` a nivel **tenant** (sin contexto académico ni vigencia) en la migración `003`. El login completa el claim `roles` desde esta tabla. **C-07 `Asignacion` extiende** con materia/comisión + `desde`/`hasta` encima (mismo patrón que `usuarios` mínima en C-03).
- **Alcance de chequeo GLOBAL**: C-04 implementa chequeos `modulo:accion` globales, fail-closed (sin permiso explícito → 403). Roles desde el JWT; **permisos efectivos resueltos desde DB** por request (nunca almacenados en el token). El refinamiento `(propio)`/contexto/vigencia (§5 de `03_actores_y_roles.md`) **se difiere a C-07** cuando exista `Asignacion`.
- **Numeración de migraciones**: C-04 usa `003` (el roadmap decía `002`, ya ocupada por C-03). Se corre +1 el resto.

## What Changes

- **NUEVA capability `rbac`**: tablas `rol`, `permiso` (`modulo:accion`), `rol_permiso` (matriz, datos) y `usuario_rol` (link mínimo tenant-level). Migración `003` + seed idempotente de los 7 roles del dominio y la matriz base de `03_actores_y_roles.md` §3.3.
- **Resolución de permisos efectivos**: servicio que, dado el usuario (roles del JWT, acotado por tenant), devuelve el set de permisos desde `rol_permiso`.
- **Guard `require_permission("modulo:accion")`**: dependency FastAPI fail-closed (403 sin permiso) en `core/permissions.py` (reemplaza el placeholder).
- **MODIFICA `authentication`**: el login resuelve los roles del usuario desde `usuario_rol` y los embebe en el claim `roles` del access token.
- Repositorios tenant-scoped para el catálogo y endpoint de lectura del catálogo/“mis permisos”.

## Impact

- Affected specs: **rbac** (nueva), **authentication** (modificada).
- Affected code (backend): `models/rol.py`, `models/permiso.py`, `models/usuario_rol.py`, `repositories/*`, `services/permission_service.py`, `core/permissions.py`, `alembic/versions/003_*`, modificación menor en `services/auth_service.py` (poblar `roles`) y `api/v1/routers` (catálogo / mis-permisos).
- Sin nuevas dependencias.
- Governance: **CRÍTICO** — requiere aprobación humana antes de implementar.
