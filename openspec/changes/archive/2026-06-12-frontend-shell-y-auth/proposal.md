# Change: frontend-shell-y-auth (C-21)

## Why

C-04 entregó RBAC y C-03 auth completa en backend; falta la SPA base para consumirla. C-21 es el shell común: login, 2FA, recuperación, cliente HTTP con refresh transparente, guards por permiso y layout adaptativo.

## What Changes

- Scaffolding `frontend/` React 18 + TypeScript + Vite + Tailwind.
- Cliente Axios centralizado (`@/shared/services/api`) con interceptor JWT + refresh en 401.
- Feature `auth`: login, 2FA, forgot/reset password, logout, contexto de sesión.
- Guards: rutas protegidas + `PermissionGate` por `modulo:accion`.
- Layout con menú derivado de `GET /api/rbac/permisos-efectivos`.
- Tests Vitest + Testing Library (login render, guard redirect, refresh mock).

## Impact

- Governance: BAJO
- Dependencias: C-04 (+ CORS en API para browser)
- Backend touch: CORS ya agregado; `/refresh` sin Bearer para refresh transparente
