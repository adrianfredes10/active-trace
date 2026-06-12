# Design — audit-log (C-05)

## Contexto

Tras C-04 (RBAC), el producto necesita trazabilidad inmutable (*trace*). E-AUD registra quién hizo qué, cuándo y con qué contexto, sin posibilidad de alterar entradas. La impersonación (RN-41) debe quedar auditada y atribuir acciones al actor real, no al usuario impersonado.

## Decisiones

### D1 — Append-only en app y DB
`audit_logs` no hereda `TimestampSoftDeleteMixin`: sin `updated_at` ni `deleted_at`. Un trigger PostgreSQL `prevent_audit_log_mutation()` rechaza UPDATE/DELETE. El repositorio solo expone `append()` y lectura tenant-scoped; no hay métodos de mutación.

### D2 — Catálogo cerrado de códigos (RN-24)
`AuditAction` (StrEnum) define los códigos permitidos. `AuditService.record()` rechaza códigos fuera del catálogo. Los módulos futuros registran acciones vía el servicio, no insertando filas directamente.

### D3 — Atribución bajo impersonación
JWT mantiene `sub` = actor real (ADMIN). Claim opcional `impersonated_sub` identifica al usuario impersonado. `AuditContext` persiste `actor_id` + `impersonado_id` en cada entrada. Los endpoints de dominio futuros usarán `AuditContext.from_user(current_user)`.

### D4 — Impersonación controlada
- Permiso `impersonacion:usar` sembrado en ADMIN.
- `POST /api/auth/impersonate/start` recibe `target_user_id`, emite access token con `impersonated_sub`.
- `POST /api/auth/impersonate/stop` limpia el claim y registra `IMPERSONACION_FINALIZAR`.
- Refresh token emite access token **sin** impersonación (sesión normal restaurada).

### D5 — API de lectura únicamente
`GET /api/audit` protegido con `auditoria:ver`. Sin ABM ni borrado de entradas. Paginación básica por tenant.

### D6 — Migración 004
Renumerada respecto al roadmap original (003 quedó para RBAC). Incluye tabla, índices y trigger.

## Riesgos / trade-offs

- **Middleware automático diferido**: C-05 no instrumenta todos los endpoints con un decorator global; los módulos de dominio llamarán `AuditService.record()` explícitamente al implementarse.
- **Impersonación y refresh**: el refresh no preserva impersonación — comportamiento intencional para limitar duración de sesión impersonada.

## Preguntas abiertas

- Panel de auditoría (C-19) consumirá `GET /api/audit`; filtros avanzados se agregan allí.
