# Tasks — estructura-academica (C-06)

## 1. Modelo y migración

- [x] 1.1 Modelos `Carrera`, `Cohorte`, `Materia` tenant-scoped
- [x] 1.2 Migración Alembic 005 con constraints únicos
- [x] 1.3 Registrar modelos en `app.models`

## 2. Capa de datos y negocio

- [x] 2.1 Repositories con scope tenant
- [x] 2.2 `EstructuraService` (CRUD + reglas unicidad / carrera activa)
- [x] 2.3 Schemas Pydantic request/response

## 3. API

- [x] 3.1 Router `/api/admin/carreras`
- [x] 3.2 Router `/api/admin/cohortes`
- [x] 3.3 Router `/api/admin/materias` con `estructura:gestionar`
- [x] 3.4 Registrar routers en `main.py`

## 4. Tests

- [x] 4.1 Tests modelos y unicidad
- [x] 4.2 Tests API CRUD + permisos + tenant isolation
- [x] 4.3 Regla carrera inactiva bloquea cohorte nueva
