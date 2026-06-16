# Proposal — C-08 `equipos-docentes`

## Why

C-07 creó el modelo `Asignacion` y CRUD básico. C-08 agrega las operaciones de negocio que los coordinadores y docentes necesitan al inicio de cada cuatrimestre: ver mis equipos, asignar en bloque, clonar entre cohortes, ajustar vigencia y exportar.

## What Changes

- `GET /api/equipos/mis-equipos` — F4.2, identidad desde sesión
- `POST /api/equipos/asignacion-masiva` — F4.4
- `POST /api/equipos/clonar` — F4.5 / RN-12
- `PATCH /api/equipos/vigencia` — F4.6
- `GET /api/equipos/exportar` — F4.7 (CSV)
- `EquiposService` + tests de integración

## Impact

- Sin migración nueva (reutiliza tabla `asignaciones`).
- Habilita flujo FL-03 setup cuatrimestre.
- Governance ALTO: operaciones masivas auditadas con `ASIGNACION_MODIFICAR`.
