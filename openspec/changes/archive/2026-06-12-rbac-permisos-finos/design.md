# Design — rbac-permisos-finos (C-04)

## Contexto

Autorización RBAC con permisos finos sobre la base multi-tenant (C-02) y la auth (C-03). La matriz rol × permiso de `03_actores_y_roles.md` §3.3 es el punto de partida; debe vivir como **datos administrables**, no hardcode.

## Decisiones

### D1 — `usuario_rol` mínimo (tenant-level) ahora; `Asignacion` (C-07) después
Para que un usuario tenga roles hoy sin la estructura académica, se crea `usuario_rol(tenant_id, usuario_id, rol_id)` sin contexto ni vigencia. C-07 introduce `Asignacion` (rol acotado a materia/comisión con `desde`/`hasta`) que se superpone. Trade-off: durante C-04→C-06 los roles son globales por tenant; aceptable porque las capacidades que requieren contexto recién aparecen con sus módulos.

### D2 — Roles en el token, permisos en la DB
El JWT lleva `roles` (claim corto, ya definido en C-03). Los **permisos NO se guardan en el token** (`08 §3.1`): `require_permission` resuelve el set efectivo por request desde `rol_permiso` para los roles del usuario, dentro de su tenant. Cache opcional por request (no entre requests) para no recalcular en guards múltiples.

### D3 — `require_permission` fail-closed
Dependency `require_permission("modulo:accion")`: obtiene `CurrentUser` (de C-03), resuelve permisos efectivos, y si el permiso pedido no está → **403**. Sin permiso explícito declarado, el endpoint no autoriza. No existe superusuario binario.

### D4 — Catálogo como datos + seed idempotente
`rol`, `permiso(modulo, accion)` con único `(tenant_id, modulo, accion)` y `(tenant_id, codigo_rol)`. La matriz §3.3 se siembra por tenant. El seed inicial corre en la migración `003` para el/los tenant(s) existentes y se expone un servicio de seed reutilizable para cuando se crea un tenant nuevo (idempotente: no duplica). NEXO se siembra como rol sin filas de capacidad en la matriz base (PA-25 abierta) — existe pero sin permisos hasta cerrar su semántica.

### D5 — Alcance GLOBAL; `(propio)`/vigencia diferido
C-04 chequea capacidad global (`calificaciones:importar`, etc.). El qualifier `(propio)` y la vigencia temporal (§5) dependen de `Asignacion`/contexto académico → se implementan en C-07 y en cada módulo de dominio. Se documenta explícitamente para no dar falsa sensación de scoping fino.

### D6 — Modificación mínima al login (C-03)
`auth_service.login`/`_issue_session` pasan de `roles=[]` a resolver los `codigo_rol` del usuario vía `usuario_rol`. Es el único cambio a código archivado, y es el punto de integración natural.

## Modelo de datos (migración 003)

- `rol(id, tenant_id, codigo, nombre, timestamps, soft-delete)` — único `(tenant_id, codigo)`.
- `permiso(id, tenant_id, modulo, accion, timestamps, soft-delete)` — único `(tenant_id, modulo, accion)`.
- `rol_permiso(id, tenant_id, rol_id, permiso_id, timestamps, soft-delete)` — único `(tenant_id, rol_id, permiso_id)`.
- `usuario_rol(id, tenant_id, usuario_id, rol_id, timestamps, soft-delete)` — único `(tenant_id, usuario_id, rol_id)`.

Todas heredan `TenantScopedMixin`. Seed de los 7 roles + permisos de la matriz §3.3.

## Riesgos / trade-offs

- **Roles globales temporales** (sin contexto) hasta C-07: una capacidad `(propio)` se comporta como global en este intervalo. Mitigación: los módulos que dependen de `(propio)` (calificaciones, comunicación) llegan después de C-07.
- **Seed en migración**: acopla datos a la migración; se mantiene idempotente y se duplica la lógica en un servicio de seed para tenants nuevos.

## Preguntas abiertas

- PA-25 (semántica de NEXO): se siembra el rol sin permisos; su matriz se completa al cerrarse.
- **Resuelta**: C-04 expone solo **lectura** (`GET /api/rbac/permisos-efectivos` y `GET /api/rbac/catalogo`) + seed. El ABM administrable completo (alta de rol/permiso, asignar roles a usuarios) queda para un change posterior de administración del tenant.
