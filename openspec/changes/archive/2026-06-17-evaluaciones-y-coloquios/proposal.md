# Proposal — C-14 `evaluaciones-y-coloquios`

## Why

Los coloquios requieren convocatorias con turnos acotados, reserva por alumno y seguimiento de métricas.

## What Changes

- Modelos `Evaluacion`, `TurnoEvaluacion`, `ConvocadoEvaluacion`, `ReservaEvaluacion`, `ResultadoEvaluacion`
- `/api/coloquios/*` — gestión (COORDINADOR/ADMIN/PROFESOR) y reserva (ALUMNO)
- Migración 012

## Impact

- Desbloquea UI de coloquios en C-23
