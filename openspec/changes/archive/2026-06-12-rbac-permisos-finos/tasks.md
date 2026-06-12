## 1. Modelos y migración 003

- [x] 1.1 (RED) Tests de modelo: `Rol` único `(tenant_id, codigo)`; `Permiso` único `(tenant_id, modulo, accion)`; `RolPermiso` único `(tenant_id, rol_id, permiso_id)`; `UsuarioRol` único `(tenant_id, usuario_id, rol_id)`; mismo código en otro tenant es válido
- [x] 1.2 (GREEN) Implementar `models/rol.py`, `models/permiso.py`, `models/rol_permiso.py`, `models/usuario_rol.py` (todos `TenantScopedMixin`)
- [x] 1.3 (GREEN) Reexportar en `models/__init__.py`
- [x] 1.4 Generar `alembic/versions/003_create_rbac_tables.py` (4 tablas + únicos)
- [x] 1.5 Verificar `alembic upgrade head` y `downgrade -1` contra la DB de test

## 2. Seed de la matriz base

- [x] 2.1 (RED) Tests: seed crea los 7 roles + permisos de la matriz §3.3; idempotente (doble ejecución no duplica); NEXO existe sin permisos
- [x] 2.2 (GREEN) Implementar `services/rbac_seed.py` (seed idempotente por tenant) con la matriz de `03_actores_y_roles.md` §3.3
- [x] 2.3 (GREEN) Invocar el seed en la migración `003` para el/los tenant(s) existentes

## 3. Repositorios (tenant-scoped)

- [x] 3.1 (RED) Test: lookup de roles/permisos solo dentro del tenant
- [x] 3.2 (GREEN) Implementar repos de `rol`, `permiso`, `rol_permiso`, `usuario_rol` (extienden `BaseRepository`)

## 4. Resolución de permisos efectivos

- [x] 4.1 (RED) Tests: unión de permisos de varios roles; acotado a tenant; usuario sin roles → set vacío
- [x] 4.2 (GREEN) Implementar `services/permission_service.py` (`effective_permissions(roles, tenant)` desde `rol_permiso`)

## 5. Guard require_permission (core/permissions.py)

- [x] 5.1 (RED) Tests: sin permiso → 403; con permiso → pasa; fail-closed sin declaración
- [x] 5.2 (GREEN) Implementar `require_permission("modulo:accion")` (usa `get_current_user` de C-03 + permission_service), reemplaza el placeholder
- [x] 5.3 (GREEN) Cache por request (no entre requests) para no recomputar en guards múltiples

## 6. Integración con login (auth_service)

- [x] 6.1 (RED) Tests: login de usuario con roles emite token con `roles` poblado; sin roles → `roles` vacío
- [x] 6.2 (GREEN) Modificar `auth_service` para resolver `codigo_rol` desde `usuario_rol` y poblar el claim `roles`

## 7. Endpoints de lectura

- [x] 7.1 (GREEN) `GET /api/rbac/permisos-efectivos` (mis permisos) y `GET /api/rbac/catalogo` (roles+permisos del tenant), protegidos por sesión
- [x] 7.2 (RED→GREEN) Tests de API: un endpoint de prueba protegido por `require_permission` devuelve 200 con permiso y 403 sin permiso

## 8. Verificación y cierre

- [x] 8.1 Suite completa con cobertura (`pytest --cov=app`): 91.5% líneas total; reglas de autorización ≥90%
- [x] 8.2 Confirmar ≤500 LOC por archivo y scope de tenant en todos los queries
- [x] 8.3 Marcar tasks y dejar listo para `/opsx:archive`
