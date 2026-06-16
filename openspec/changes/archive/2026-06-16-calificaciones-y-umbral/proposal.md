# Proposal — C-10 `calificaciones-y-umbral`

## Why

Con padrón cargado (C-09), el docente necesita importar notas del LMS, derivar aprobado según RN-01/02/03 y configurar umbral por asignación sin afectar a otros docentes.

## What Changes

- Modelos `Calificacion` + `UmbralMateria` (migración 008)
- Parser CSV: columnas `(Real)` numéricas, textuales RN-02
- `POST /api/calificaciones/preview`, `/importar`, `/finalizacion/preview`
- `PUT/GET /api/calificaciones/umbral` por asignación
- Audit `CALIFICACIONES_IMPORTAR`
- Permiso `calificaciones:importar` (ya en RBAC seed)

## Impact

- Desbloquea C-11 (análisis atrasados y reportes)
- Sin frontend en este change
