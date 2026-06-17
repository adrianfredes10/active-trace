# Proposal — C-19 `panel-auditoria-metricas`

## Why

Supervisión de actividad docente y trazabilidad operativa (F9.1, F9.2).

## What Changes

- `/api/auditoria/*` — acciones por día, comunicaciones por docente, interacciones, log filtrado
- Scope `(propio)` para COORDINADOR por materias asignadas
- Límite log configurable (default 200, máx 500)
