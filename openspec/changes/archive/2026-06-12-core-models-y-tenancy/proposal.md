## Why

C-01 dejó el cimiento ejecutable (FastAPI async, engine SQLAlchemy 2.0, `core/` con slots reservados) pero **sin modelo de datos ni aislamiento de tenant**. Toda la cadena de Fase 1 (C-03 auth, C-04 RBAC) y los módulos de dominio dependen de tres invariantes que aún no existen en código: (1) la entidad `Tenant` como raíz, (2) un mixin base común a toda entidad (`id` UUID, `tenant_id`, timestamps, soft delete), y (3) un repository genérico que filtra por `tenant_id` **por defecto** (ADR-002 row-level). Sin esto, cualquier modelo que se cree después nacería sin scope de tenant — un bug de seguridad que falla en code review. También se necesita el helper de cifrado AES-256 para los atributos `[cifrado]` (DNI, CUIL, CBU, email PII) antes de modelar `Usuario` en C-07.

Governance **CRÍTICO**: este change define el corazón multi-tenant del sistema. Toca seguridad y aislamiento de datos; se implementa con TDD estricto y los tests de aislamiento son obligatorios.

## What Changes

- **Entidad `Tenant`** raíz (E0): identidad de cada institución. Tabla `tenants` con `id` (UUID), `nombre`, `slug` único, `estado`, timestamps. NO lleva `tenant_id` (es la raíz).
- **Mixin base** (`models/base.py`) que toda entidad de dominio hereda: `id` (UUID v4), `tenant_id` (FK → tenants), `created_at`, `updated_at` (auto), `deleted_at` (nullable, soft delete). Provee la convención común del modelo (`knowledge-base/04` §Convenciones).
- **Repository genérico tenant-scoped** (`repositories/base.py`): clase base que recibe el `tenant_id` del contexto y filtra **todas** las queries por `tenant_id` + `deleted_at IS NULL` por defecto. Métodos: `get`, `list`, `add`, `soft_delete`. Un query sin scope de tenant no es posible desde la API del repo.
- **Helper de cifrado AES-256** (`core/security.py`, slot reservado en C-01): funciones `encrypt(plaintext) -> str` / `decrypt(ciphertext) -> str` usando `ENCRYPTION_KEY` (32 chars). Para atributos `[cifrado]`; nunca loguea valores en claro. Se provee también un `EncryptedString` TypeDecorator de SQLAlchemy para cifrado transparente en columnas.
- **Soft delete transversal**: borrado lógico vía `deleted_at`; el repository base excluye los borrados por defecto. Nunca hard delete.
- **Alembic — Migración 001 `tenant`**: primera migración de dominio (crea `tenants`). Convención: una migración por cambio de schema.
- **Tests (TDD, sin mock de DB)**: aislamiento multi-tenant (tenant A no ve datos de tenant B), soft delete (excluido por defecto, recuperable explícito), cifrado round-trip (`decrypt(encrypt(x)) == x` y ciphertext ≠ plaintext), mixin timestamps (auto-set en insert/update).

No hay cambios BREAKING: C-01 dejó los slots reservados; este change los rellena sin reorganizar el árbol. `core/security.py` pasa de placeholder a implementado (solo cifrado; JWT/Argon2 siguen reservados para C-03).

## Capabilities

### New Capabilities

- `core-data-model`: entidad `Tenant` raíz y el mixin base (`id` UUID, `tenant_id`, `created_at`, `updated_at`, `deleted_at`) que materializa las convenciones del modelo de datos para toda entidad de dominio.
- `tenant-isolation`: repository genérico que aplica scope de `tenant_id` por defecto en todas las queries (ADR-002 row-level); los datos nunca cruzan tenants.
- `field-encryption`: utilidad de cifrado AES-256 en reposo para atributos PII/secretos (`[cifrado]`), con tipo de columna SQLAlchemy para cifrado transparente; nunca expone valores en claro en logs.
- `database-migrations`: migración Alembic 001 que crea la tabla `tenants`, estableciendo la convención de una migración por cambio de schema.

### Modified Capabilities

<!-- Ninguna spec previa se modifica: las capabilities de C-01 (app-scaffold, etc.) siguen vigentes sin cambios. -->

## Impact

- **Nuevo código**: `app/models/base.py`, `app/models/tenant.py`, `app/repositories/base.py`, implementación de `app/core/security.py` (solo cifrado), `alembic/versions/001_*.py`, y sus tests.
- **`core/security.py`**: deja de ser placeholder; implementa cifrado AES-256 (JWT/Argon2 quedan para C-03).
- **Dependencias**: `cryptography` (ya presente como transitiva de python-jose) se declara explícita para el helper AES-256-GCM.
- **Habilita** a C-03 (`auth-jwt-2fa`) y a toda la Fase 1: ningún modelo de dominio puede crearse sin el mixin base y el repo tenant-scoped.
- **Governance**: CRÍTICO — multi-tenancy, aislamiento de datos y cifrado de PII. Requiere aprobación humana antes de implementar y tests de aislamiento obligatorios.
