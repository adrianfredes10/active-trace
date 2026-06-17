# Proposal — C-13 `encuentros-y-guardias`

## Why

Docentes y tutores necesitan programar clases virtuales recurrentes y registrar guardias de atención.

## What Changes

- Modelos `SlotEncuentro`, `InstanciaEncuentro`, `Guardia` (migración 011)
- RN-13: generación automática de N instancias semanales
- `/api/encuentros/*` (recurrente, único, editar, HTML, admin)
- `/api/guardias/*` (registro, listado, export CSV)

## Impact

- Paralelo al camino crítico; desbloquea UI de encuentros en C-22/C-23
