# Proposal — C-09 `padron-ingesta-moodle`

## Why

Sin padrón no hay alumnos contra los que importar calificaciones ni detectar atrasados. C-09 implementa el modelo versionado E6, import manual (CSV/XLSX) y sync Moodle WS.

## What Changes

- Modelos `VersionPadron` + `EntradaPadron` (migración 007)
- `POST /api/padron/preview`, `/importar`, `/moodle/sync`, `DELETE /materias/{id}/datos`
- Permisos `padron:importar`, `padron:vaciar`
- Cliente `integrations/moodle_ws.py` (502 si Moodle cae)
- Audit `PADRON_CARGAR`

## Impact

- Desbloquea C-10 (calificaciones)
- Sin cambios en frontend en este change
