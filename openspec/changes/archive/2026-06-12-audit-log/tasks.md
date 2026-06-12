## 1. Modelo y migración 004
- [x] 1.1 Tests modelo + trigger append-only
- [x] 1.2 Modelo AuditLog + migración 004 con trigger anti-mutación

## 2. Servicio de auditoría
- [x] 2.1 AuditAction enum + AuditService.record + tests
- [x] 2.2 AuditLogRepository append-only tenant-scoped

## 3. Impersonación
- [x] 3.1 JWT impersonated_sub + CurrentUser + seed impersonacion:usar
- [x] 3.2 start/stop endpoints + audit events + tests

## 4. API y cierre
- [x] 4.1 GET /api/audit + tests API
- [x] 4.2 Suite ≥80%, archive
