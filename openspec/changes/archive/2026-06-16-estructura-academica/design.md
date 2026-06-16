# Design — estructura-academica (C-06)

## Decisiones

### D1 — PA-01 cerrada por ADR-006
`Materia` = catálogo único por tenant (`codigo` único). `Dictado` (materia × carrera × cohorte) **no** entra en C-06.

### D2 — PA-07: cohorte → carrera (1:N)
Una cohorte pertenece a exactamente una carrera. Unicidad `(tenant_id, carrera_id, nombre)`.

### D3 — Estado activa/inactiva
`Carrera.estado` enum `activa|inactiva`. Cohorte nueva requiere carrera activa (RN de CHANGES).

### D4 — Permiso
ABM protegido con `estructura:gestionar` (sembrado en ADMIN/COORDINADOR según matriz §3.3 — verificar seed).

### D5 — Migración 005
Tablas: `carreras`, `cohortes`, `materias`. Índices únicos parciales con soft delete vía application layer (unique constraints on codigo/nombre).

## Modelo

```
Carrera: codigo, nombre, estado
Cohorte: carrera_id, nombre, fecha_inicio (optional), estado
Materia: codigo, nombre, descripcion (optional), estado
```

Todos `TenantScopedMixin`.
