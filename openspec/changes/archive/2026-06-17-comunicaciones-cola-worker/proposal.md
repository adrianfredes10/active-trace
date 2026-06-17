# Proposal — C-12 `comunicaciones-cola-worker`

## Why

Tras detectar atrasados (C-11), el docente debe poder enviar recordatorios con preview obligatorio, cola auditable y aprobación de envíos masivos.

## What Changes

- Modelo `Comunicacion` + migración 010
- `Tenant.aprobacion_masiva_comunicaciones` (RN-17 configurable)
- `POST /api/comunicaciones/preview`, `/enviar`, aprobar/cancelar lote e individual
- Worker `procesar_pendientes` (RN-15: Pendiente→Enviando→Enviado/Error)
- Destinatario cifrado AES-256, audit `COMUNICACION_ENVIAR`

## Impact

- Cierra camino crítico importar→analizar→comunicar
- Desbloquea C-22 frontend docente
