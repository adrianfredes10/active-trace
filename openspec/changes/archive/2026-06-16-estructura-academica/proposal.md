# Change: estructura-academica (C-06)

## Why

GATE 4 habilita el dominio académico. Sin Carrera/Cohorte/Materia no hay C-07 (usuarios/asignaciones), ni ingesta Moodle, ni el camino crítico. ADR-006 cierra PA-01: `Materia` es catálogo único; `Dictado` (instancia) llega en un change posterior.

## What Changes

- Modelos `Carrera`, `Cohorte`, `Materia` tenant-scoped con soft delete.
- PA-07 resuelta en diseño: **cohorte pertenece a una carrera** (`carrera_id` FK obligatorio).
- ABM admin: `/api/admin/carreras`, `/api/admin/cohortes`, `/api/admin/materias` con `estructura:gestionar`.
- Migración **005**.
- Tests: CRUD, unicidad, aislamiento tenant, carrera inactiva bloquea cohortes nuevas.

## Impact

- Governance: MEDIO
- Dependencias: C-04
- Desbloquea: C-07, C-15, C-17, camino crítico
