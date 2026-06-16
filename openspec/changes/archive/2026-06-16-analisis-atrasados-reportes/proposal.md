# Proposal — C-11 `analisis-atrasados-reportes`

## Why

Con calificaciones importadas (C-10), docentes y coordinación necesitan detectar atrasados, rankings y reportes sin recalcular en el router.

## What Changes

- `AnalisisService` + reglas puras RN-06/RN-09
- `GET /api/analisis/atrasados`, `/ranking`, `/reporte-rapido`, `/notas-finales`
- `PUT /api/analisis/agrupaciones` (JSONB en `umbrales_materia`, migración 009)
- `GET /api/analisis/sin-corregir` + export CSV (RN-08 textual)
- `GET /api/analisis/monitor/seguimiento` (F2.8) y `/monitor/general` (F2.7/F2.9)
- Permiso `atrasados:ver`

## Impact

- Desbloquea C-12 (comunicaciones a atrasados)
- Sin frontend en este change
