## 1. Dependencias y base declarativa

- [x] 1.1 Declarar `cryptography` como dependencia explícita en `backend/pyproject.toml` (helper AES-256-GCM)
- [x] 1.2 Verificar que existe la `Base` declarativa de SQLAlchemy (C-01) y que `alembic/env.py` apunta a `Base.metadata`; crear `app/models/__init__.py` que reexporte los modelos para el autogenerate

## 2. Mixins base (models/base.py)

- [x] 2.1 (RED) Escribir test que verifique que una entidad de prueba con el mixin obtiene `id` UUID autogenerado, `created_at`/`updated_at` poblados en alta y `deleted_at` nulo
- [x] 2.2 (GREEN) Implementar `TimestampSoftDeleteMixin` (`id` UUID v4 default, `created_at` server_default, `updated_at` onupdate, `deleted_at` nullable)
- [x] 2.3 (GREEN) Implementar `TenantScopedMixin(TimestampSoftDeleteMixin)` agregando `tenant_id` (UUID, FK → `tenants.id`, indexado, not null)
- [x] 2.4 (TRIANGULATE) Agregar test que verifique que `updated_at` cambia al modificar y `created_at` permanece estable

## 3. Entidad Tenant (models/tenant.py)

- [x] 3.1 (RED) Escribir test que persista un `Tenant` válido y verifique `id` UUID, `estado` default `Activo` y timestamps; y test que falle al duplicar `slug`
- [x] 3.2 (GREEN) Implementar `Tenant` heredando SOLO `TimestampSoftDeleteMixin` (sin `tenant_id`): columnas `nombre`, `slug` (único), `estado` (enum)
- [x] 3.3 (TRIANGULATE) Verificar que `Tenant` NO tiene columna `tenant_id`

## 4. Cifrado AES-256 (core/security.py)

- [x] 4.1 (RED) Escribir test de round-trip (`decrypt(encrypt(x)) == x`), de que el ciphertext ≠ plaintext, y de que descifrar un token alterado falla
- [x] 4.2 (GREEN) Implementar `encrypt`/`decrypt` con AES-256-GCM usando `ENCRYPTION_KEY` (nonce por operación, salida base64 autenticada)
- [x] 4.3 (GREEN) Implementar `EncryptedString` TypeDecorator (cifra en bind, descifra en result)
- [x] 4.4 (RED→GREEN) Test de persistencia transparente: una columna `EncryptedString` guarda ciphertext en DB y devuelve plaintext al leer (DB real)
- [x] 4.5 (TRIANGULATE) Verificar que los valores `[cifrado]` no aparecen en `__repr__`/logs de la entidad

## 5. Repository genérico tenant-scoped (repositories/base.py)

- [x] 5.1 (RED) Escribir test de aislamiento: entidad creada bajo tenant A no es visible para un repo del tenant B (`get` y `list`)
- [x] 5.2 (GREEN) Implementar `BaseRepository(session, tenant_id)` con `get`, `list`, `add` (todas con `WHERE tenant_id = :tenant_id AND deleted_at IS NULL`)
- [x] 5.3 (GREEN) `add` fija `entity.tenant_id` desde el contexto, ignorando el `tenant_id` entrante
- [x] 5.4 (GREEN) Implementar `soft_delete` (setea `deleted_at`, nunca DELETE físico) y `get_including_deleted` (escape hatch explícito)
- [x] 5.5 (TRIANGULATE) Tests: alta con `tenant_id` ajeno termina con el tenant del contexto; soft delete excluye por defecto y es recuperable por el método explícito

## 6. Migración Alembic 001

- [x] 6.1 Generar `alembic/versions/001_create_tenants.py` (autogenerate o manual) que cree `tenants` con columnas e índice único de `slug`
- [x] 6.2 Verificar `alembic upgrade head` crea la tabla y `downgrade -1` la elimina contra la DB de test
- [x] 6.3 Documentar la convención "una migración por cambio de schema" en el README del backend o en `alembic/README`

## 7. Verificación y cierre

- [x] 7.1 Ejecutar la suite completa con cobertura (`pytest --cov=app`) y confirmar ≥80% líneas / ≥90% en las reglas de aislamiento y cifrado
- [x] 7.2 Confirmar que ningún archivo supera 500 LOC y que no hay queries de dominio sin scope de tenant
- [x] 7.3 Marcar todas las tareas y dejar el change listo para `/opsx:archive`
