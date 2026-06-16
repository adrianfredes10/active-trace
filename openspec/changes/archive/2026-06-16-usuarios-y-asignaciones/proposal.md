# Proposal — C-07 `usuarios-y-asignaciones`

## Why

`Usuario` hoy solo contiene los campos de autenticación (email cifrado, password, 2FA). No tiene nombre, DNI, CUIL, CBU, legajo ni ningún dato de negocio. Tampoco existe el modelo `Asignacion`, que es el eje del modelo de autorización: vincula usuarios con roles dentro de un contexto académico concreto (materia/carrera/cohorte) con vigencia temporal. Sin esto, ningún módulo posterior puede saber "qué docente está asignado a qué materia", ni calcular equipos docentes, liquidaciones, umbrales, guardias, etc.

## What Changes

- **`Usuario` extendido**: agrega campos de negocio (nombre, apellidos) y PII cifrada (dni, cuil, cbu, alias_cbu); legajo como atributo opcional; facturador; estado Activo/Inactivo.
- **`Asignacion`**: nuevo modelo que vincula Usuario ↔ Rol ↔ contexto (materia/carrera/cohorte), con vigencia `desde/hasta` y `responsable_id`.
- **Migración 006**: ALTER TABLE usuarios + CREATE TABLE asignaciones.
- **Endpoints ABM**: `/api/admin/usuarios` (guard `usuarios:gestionar`) y `/api/asignaciones` (guard `equipos:asignar`).
- **Tests**: PII no expuesta en logs ni respuestas; asignación vencida no autoriza; aislamiento tenant; multi-rol.

## Impact

- Toca tabla `usuarios` existente (ALTER, no DROP/CREATE — filas de auth se conservan).
- Habilita C-08 (equipos), C-09 (padrón), C-10 (calificaciones) y toda la FASE 4.
- Governance CRÍTICO: aprobación explícita requerida antes de codear.
