# Tasks — C-07 `usuarios-y-asignaciones`

## 1. Tests (RED primero — TDD)

- [ ] 1.1 (RED) `tests/test_usuario_model.py`: Usuario con PII cifrada round-trip (dni, cuil, cbu, alias_cbu nunca expuestos en repr/log)
- [ ] 1.2 (RED) `tests/test_asignacion_model.py`: Asignacion vigente otorga permiso; vencida no; sin fecha hasta = abierta
- [ ] 1.3 (RED) `tests/test_usuario_api.py`: CRUD `/api/admin/usuarios` con guard `usuarios:gestionar`; PII no en respuesta
- [ ] 1.4 (RED) `tests/test_asignacion_api.py`: CRUD `/api/asignaciones` con guard `equipos:asignar`; tenant isolation

## 2. Migración 006

- [ ] 2.1 `alembic/versions/006_extend_usuarios_asignaciones.py`: ALTER TABLE usuarios (columnas nullable con default NULL); CREATE TABLE asignaciones con constraints y FKs

## 3. Modelos

- [ ] 3.1 Extender `app/models/usuario.py`: nombre, apellidos, dni `[cifrado]`, cuil `[cifrado]`, cbu `[cifrado]`, alias_cbu `[cifrado]`, banco, regional, legajo, legajo_profesional, facturador, estado enum
- [ ] 3.2 Nuevo `app/models/asignacion.py`: Asignacion con usuario_id, rol enum (semilla C-04), materia_id, carrera_id, cohorte_id, comisiones JSONB, responsable_id, desde, hasta; propiedad `vigente` derivada
- [ ] 3.3 Registrar Asignacion en `app/models/__init__.py`

## 4. Repositories

- [ ] 4.1 Extender `app/repositories/usuario_repository.py`: métodos `get_by_email_hash`, `list_activos`, `create`, `update`, `deactivate` (soft delete)
- [ ] 4.2 Nuevo `app/repositories/asignacion_repository.py`: `list_vigentes_by_usuario`, `list_by_materia`, `list_by_tenant`, `create`, `update_vigencia`, `soft_delete`

## 5. Service

- [ ] 5.1 Nuevo `app/services/usuario_service.py`: `crear_usuario`, `actualizar_usuario`, `desactivar_usuario`; PII solo en args/retornos del service, nunca en logs
- [ ] 5.2 Nuevo `app/services/asignacion_service.py`: `crear_asignacion`, `actualizar_vigencia`, `anular_asignacion`; validar unicidad contextual

## 6. Schemas Pydantic

- [ ] 6.1 `app/schemas/usuario.py`: `UsuarioCreate`, `UsuarioUpdate`, `UsuarioResponse` (PII excluida de response salvo campos no sensibles); `extra='forbid'`
- [ ] 6.2 `app/schemas/asignacion.py`: `AsignacionCreate`, `AsignacionUpdate`, `AsignacionResponse`; `extra='forbid'`

## 7. Routers

- [ ] 7.1 `app/api/v1/routers/usuarios.py`: GET/POST `/api/admin/usuarios`, GET/PUT/DELETE `/api/admin/usuarios/{id}`; guard `usuarios:gestionar`; audit `USUARIO_CREAR`/`USUARIO_MODIFICAR`
- [ ] 7.2 `app/api/v1/routers/asignaciones.py`: GET/POST `/api/asignaciones`, GET/PUT/DELETE `/api/asignaciones/{id}`; guard `equipos:asignar`; audit `ASIGNACION_MODIFICAR`
- [ ] 7.3 Registrar routers en `app/main.py`

## 8. GREEN + TRIANGULATE

- [ ] 8.1 Correr todos los tests del paso 1 → verde
- [ ] 8.2 Triangular: PII nunca en logs (capturar output del logger), asignación vencida → 403 en endpoint con vigencia checks
