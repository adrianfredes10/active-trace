# Proposal — C-16 `tareas-internas`

## Why

Coordinación interna entre docentes requiere tareas asignables con workflow y comentarios.

## What Changes

- Modelos `Tarea`, `ComentarioTarea` (migración 014)
- `/api/tareas/*` — mis tareas, admin, delegar, estados, comentarios
- Permiso `tareas:gestionar` también para TUTOR (F8.1)
