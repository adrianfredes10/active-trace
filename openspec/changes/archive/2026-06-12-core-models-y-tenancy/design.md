## Context

C-02 materializa el corazón multi-tenant de activia-trace. El contrato ya está cerrado: **ADR-002 row-level** (una sola DB, `tenant_id` en toda tabla, repositories filtran por tenant por defecto — `docs/ARQUITECTURA.md §6, §10`), **soft delete siempre** (`knowledge-base/08 §6`), **PII cifrada en reposo con AES-256** (`docs/ARQUITECTURA.md §5.4`), e **identidad por UUID interno** (`knowledge-base/04 §Supuestos`). C-01 dejó los slots `core/security.py`, `core/tenancy.py`, `repositories/`, `models/` reservados. Este change los rellena.

Governance **CRÍTICO**: la lógica de aislamiento es invariante de seguridad. TDD estricto; los tests de cross-tenant son la red de seguridad principal.

## Goals / Non-Goals

**Goals:**

- Entidad `Tenant` raíz + mixin base reutilizable (`id` UUID, `tenant_id`, `created_at`, `updated_at`, `deleted_at`).
- Repository genérico que filtra por `tenant_id` y excluye soft-deleted **por defecto**, sin forma de saltarse el scope accidentalmente.
- Helper de cifrado AES-256 + tipo de columna SQLAlchemy para cifrado transparente de atributos `[cifrado]`.
- Migración Alembic 001 (`tenants`) y convención de una migración por cambio de schema.
- Tests sin mock de DB: aislamiento cross-tenant, soft delete, cifrado round-trip, timestamps automáticos.

**Non-Goals:**

- Modelos de dominio concretos (`Carrera`, `Usuario`, etc.) → C-06/C-07 en adelante.
- Resolución del `tenant_id` desde el JWT (`get_tenant` / `get_current_user`) → C-03. Aquí el `tenant_id` se inyecta como parámetro explícito al repository; el wiring con la sesión llega con auth.
- Hashing de passwords (Argon2id) y JWT → C-03. `core/security.py` en C-02 implementa SOLO cifrado AES-256.
- RBAC, permisos, audit log → C-04/C-05.

## Decisions

### D1 — `Tenant` como raíz sin `tenant_id`

`Tenant` es la única entidad que NO hereda el mixin con `tenant_id` (sería autorreferencia inútil). Hereda un mixin más chico (`id` UUID + timestamps + soft delete). Tabla `tenants`: `id` (UUID PK), `nombre` (texto), `slug` (texto, único global — selector legible de instancia), `estado` (enum `Activo|Inactivo`), `created_at`, `updated_at`, `deleted_at`.

**Por qué `slug` único global**: identifica al tenant de forma estable y legible (subdominios, routing futuro) sin exponer el UUID. No es credencial.

### D2 — Dos mixins: `TimestampMixin` + `TenantMixin`

Para no forzar `tenant_id` en `Tenant`, se parte en dos:

- `TimestampSoftDeleteMixin`: `id` (UUID v4, `default=uuid4`), `created_at` (server_default now), `updated_at` (onupdate now), `deleted_at` (nullable). Lo hereda **toda** entidad, incluido `Tenant`.
- `TenantScopedMixin(TimestampSoftDeleteMixin)`: agrega `tenant_id` (UUID, FK → `tenants.id`, indexado, not null). Lo hereda toda entidad de dominio EXCEPTO `Tenant`.

**Alternativa descartada**: un único mixin con `tenant_id` nullable. Se descarta: `tenant_id` nullable abre la puerta a entidades sin scope — exactamente el bug que debemos prevenir. Mejor que `Tenant` simplemente no tenga la columna.

### D3 — Repository genérico tenant-scoped (fail-safe por construcción)

`BaseRepository` se instancia **siempre** con `(session, tenant_id)`. No existe constructor sin `tenant_id`. Todas las queries internas aplican `WHERE tenant_id = :tenant_id AND deleted_at IS NULL`:

- `get(id)` → una entidad del tenant, no borrada, o `None`.
- `list(**filters)` → lista del tenant, no borradas.
- `add(entity)` → fija `entity.tenant_id = self.tenant_id` antes de persistir (ignora cualquier `tenant_id` que venga seteado: la identidad de tenant la define el contexto, no el dato de entrada — análogo a la regla de oro de identidad).
- `soft_delete(entity)` → setea `deleted_at = now()`, nunca DELETE físico.
- `get_including_deleted(id)` → escape hatch explícito y nombrado para casos de auditoría/restore; el nombre deja claro que se sale del default.

`Tenant` no usa `BaseRepository` (no tiene `tenant_id`); usa un repo propio mínimo o queries directas en su service (se resuelve en apply, no bloqueante).

**Por qué clase base y no mixin de queries sueltas**: centralizar el scope en un solo lugar testeable; un repo de dominio que extienda `BaseRepository` hereda el aislamiento gratis y no puede olvidarlo.

### D4 — Cifrado AES-256-GCM con `EncryptedString` TypeDecorator

`core/security.py` implementa:

- `encrypt(plaintext: str) -> str` y `decrypt(token: str) -> str` usando **AES-256-GCM** (de `cryptography`), con la clave de 32 bytes de `ENCRYPTION_KEY`. GCM aporta autenticación (detecta manipulación). El nonce (12 bytes) se genera por operación y se prepende al ciphertext; salida en base64.
- `EncryptedString(TypeDecorator)`: tipo de columna SQLAlchemy que cifra en `process_bind_param` (escritura) y descifra en `process_result_value` (lectura). Las columnas `[cifrado]` (DNI, CUIL, CBU, email PII) lo usan → cifrado transparente, el resto del código maneja texto plano en memoria pero la DB guarda ciphertext.

**Por qué GCM y no CBC**: GCM es AEAD (cifra + autentica) y es el estándar moderno; CBC requiere HMAC aparte y es más fácil de implementar mal.

**Nunca en logs**: los valores `[cifrado]` no se incluyen en `repr`/logs. El logger JSON de C-01 ya filtra; los modelos no exponen estos campos en `__repr__`.

**Trade-off (búsqueda)**: GCM con nonce aleatorio hace el ciphertext no determinista → no se puede hacer `WHERE email = :x` directo sobre la columna cifrada. Para `email` (que necesita unicidad/búsqueda en C-07) se evaluará un hash determinista ciego (blind index) en ese change. C-02 solo entrega el helper; la estrategia de búsqueda sobre PII es problema de C-07, no del cimiento.

### D5 — Migración Alembic 001

`alembic/env.py` ya quedó configurado async en C-01 con `target_metadata = Base.metadata`. C-02 importa los modelos en el `env.py` (o un `models/__init__.py` que los agregue) para que el autogenerate los detecte, y genera `001_create_tenants.py` (crea `tenants` con sus columnas + índices). Convención: **una migración por cambio de schema**; los modelos de dominio futuros traen su propia migración.

### D6 — `tenant_id` inyectado, no resuelto (aún)

En C-02 el `tenant_id` llega al repository como parámetro explícito (en tests, un UUID fijo). La resolución desde el JWT (`get_tenant`) es de C-03. Esto mantiene C-02 enfocado en persistencia + aislamiento sin acoplarse a auth, y deja el contrato claro: quien construya el repo debe pasar un `tenant_id` válido del contexto de sesión.

## Risks / Trade-offs

- **[Un dev podría crear un modelo de dominio heredando el mixin equivocado]** → Mitigación: `TenantScopedMixin` es el default documentado; test de scaffold que verifique que los modelos de dominio (cuando existan) llevan `tenant_id`. En C-02 solo está `Tenant`, que correctamente NO lo lleva.
- **[Cifrado no determinista rompe búsqueda por PII]** → Aceptado y diferido a C-07 (blind index para `email`). C-02 entrega solo el helper.
- **[`ENCRYPTION_KEY` mal rotada haría ilegibles los datos]** → Fuera de scope; la rotación de claves es operación de despliegue. Se documenta que cambiar la clave invalida el ciphertext existente.
- **[Tests requieren PostgreSQL real]** → Igual que C-01: se usa el `postgres` de compose / DB de test. No se mockea la DB (regla dura: mockear la DB invalida el test de aislamiento).
- **[Soft delete + unicidad]** → Un `slug` de tenant borrado bloquearía reusar el slug. Se acepta para C-02 (la unicidad incluye filas soft-deleted); si se necesita reuso, se resuelve con índice parcial `WHERE deleted_at IS NULL` cuando aparezca el caso.

## Migration Plan

Primer modelo del sistema, sin estado previo. Deploy: `alembic upgrade head` crea `tenants`. Rollback: `alembic downgrade -1` la elimina (sin datos productivos aún). Los changes siguientes encadenan sus migraciones sobre la 001.

## Open Questions

- **Repo de `Tenant`**: ¿repo dedicado mínimo o queries en su service? Decisión menor, se cierra en apply. No bloquea.
- **Blind index para `email`**: estrategia de búsqueda sobre PII cifrada → se define en C-07 (usuarios), no aquí.
- **Índice parcial para unicidad con soft delete**: se introduce solo cuando un caso real requiera reusar un valor único de una fila borrada.
