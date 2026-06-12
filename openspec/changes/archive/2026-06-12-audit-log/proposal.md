# Change: audit-log (C-05)

## Why

C-04 habilitó RBAC; falta la trazabilidad inmutable que define el producto (*trace*). C-05 implementa E-AUD append-only, el servicio de registro con catálogo cerrado de códigos, e impersonación controlada (RN-41) con eventos `IMPERSONACION_INICIAR` / `IMPERSONACION_FINALIZAR`.

## What Changes

- Modelo `AuditLog` append-only (migración **004**; CHANGES decía 003, renumerada tras RBAC).
- Trigger DB que rechaza UPDATE/DELETE en `audit_logs`.
- `AuditService.record()` + enum `AuditAction` (catálogo cerrado RN-24).
- Extensión JWT: claim opcional `impersonated_sub`; `CurrentUser.impersonated_id`.
- Endpoints impersonación: `POST /api/auth/impersonate/start|stop` con `impersonacion:usar`.
- `GET /api/audit` con `auditoria:ver`.
- Seed: permiso `impersonacion:usar` en ADMIN.

## Impact

- Governance: CRÍTICO
- Dependencias: C-04
