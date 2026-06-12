## Why

C-02 dejó el cimiento de datos (Tenant, mixins, repo tenant-scoped, cifrado AES-256) pero el sistema todavía **no tiene autenticación**: cualquier endpoint es anónimo. Toda la plataforma exige sesión salvo el propio flujo de login y recuperación (`03_actores_y_roles §6`). C-03 implementa la **regla de oro de identidad** (`07_flujos_principales` FL-01): la identidad, el tenant y los roles del usuario salen **exclusivamente del JWT verificado server-side**, nunca de un parámetro de la petición.

C-03 también habilita el resto del camino crítico: C-04 (RBAC) necesita `get_current_user` para resolver permisos; todo módulo de dominio necesita saber quién pide y desde qué tenant.

**Decisión de borde C-03 ↔ C-07 (acordada)**: la entidad `Usuario` completa es de C-07, pero auth necesita persistir credenciales ahora. C-03 crea una tabla `usuarios` **mínima** (solo lo que auth requiere) y C-07 la **extiende** (ALTER) con los campos de negocio/PII y agrega `asignacion`. El blind index de email (lookup determinista) se introduce en C-03 porque login es su primer consumidor.

Governance **CRÍTICO**: define autenticación, sesión y cifrado de credenciales. TDD estricto; aprobación humana antes de implementar.

## What Changes

- **Tabla `usuarios` mínima** (auth-only, tenant-scoped): `email` (cifrado AES-256), `email_hash` (blind index HMAC determinista, único por tenant — habilita login por email sobre dato cifrado), `password_hash` (Argon2id), `is_active`, `two_factor_enabled`, `totp_secret` (cifrado, nullable) + mixin base (id UUID, timestamps, soft delete).
- **Tabla `refresh_tokens`**: `token_hash`, `expires_at`, `revoked_at`, `replaced_by_id` (cadena de rotación). Solo se almacena el HASH del token, nunca el valor.
- **Tabla `password_reset_tokens`**: `token_hash`, `expires_at`, `used_at` (un solo uso, expiración corta).
- **`Migración 002`** crea las tres tablas. (Renumera las migraciones posteriores del roadmap: RBAC pasa a 003, etc.)
- **`core/security.py` (extiende C-02)**: `hash_password`/`verify_password` (Argon2id), `create_access_token`/`create_refresh_token`/`decode_token` (JWT firmado, claims mínimos `sub`/`tenant_id`/`roles`/`exp`/`type`), `email_blind_index` (HMAC-SHA256 con pepper de `SECRET_KEY`), helpers TOTP (enrolar/verificar).
- **`core/dependencies.py`**: `get_current_user` (resuelve identidad + tenant desde el Bearer token verificado; fail-closed 401). Realiza el slot reservado en C-01.
- **Endpoints `/api/auth`**:
  - `POST /login` — email + password (Argon2id). Si el usuario tiene 2FA → devuelve un **challenge** (token intermedio de corta vida) y exige TOTP antes de emitir sesión. Si no → emite access (15 min) + refresh (rotación).
  - `POST /2fa/verify` — valida TOTP del challenge y emite la sesión.
  - `POST /2fa/enroll` + `POST /2fa/confirm` — enrolar/activar 2FA (autenticado).
  - `POST /refresh` — rota el refresh (el usado se revoca); **reuso de un refresh revocado invalida toda la cadena** (detección de robo) → 401.
  - `POST /logout` — revoca la sesión activa.
  - `POST /forgot` — emite token de reset de un solo uso (se persiste su hash; el envío de email queda como punto de integración, no se manda en C-03).
  - `POST /reset` — consume el token y setea nuevo password.
- **Rate limiting** en login: 5 intentos / 60 s por `IP + email` (limiter en proceso con punto de extensión a store compartido).
- **Tests (TDD, DB real)**: login OK/KO, refresh rotation + detección de reuso, flujo 2FA completo, reset de un solo uso (segundo uso falla), rate limit, e identidad inmutable (un `user_id`/`tenant_id` en la petición NO cambia la identidad de la sesión).

## Capabilities

### New Capabilities

- `authentication`: login con email+password (Argon2id), emisión de JWT (access corto + refresh con rotación), logout, y la regla de oro de identidad vía `get_current_user`.
- `two-factor-auth`: 2FA TOTP opcional por usuario (enrolar, activar, verificar) como gate entre la validación de credenciales y la emisión de sesión.
- `password-recovery`: recuperación de contraseña con token de un solo uso y expiración corta (`forgot`/`reset`).
- `auth-storage`: tabla `usuarios` mínima (auth-only) con email cifrado + blind index, y tablas de sesión (`refresh_tokens`) y recuperación (`password_reset_tokens`); migración 002.

### Modified Capabilities

- `field-encryption`: se añade el blind index determinista (HMAC) como complemento del cifrado AES-256 para permitir lookup sobre atributos cifrados (caso email en login). El cifrado en reposo no cambia; se suma la capacidad de búsqueda ciega.

## Impact

- **Nuevo código**: `app/models/usuario.py`, `app/models/auth_token.py` (refresh + reset), ampliación de `app/core/security.py`, `app/core/dependencies.py` (`get_current_user`), `app/services/auth_service.py`, `app/repositories/usuario_repository.py` + repos de tokens, `app/api/v1/routers/auth.py`, `app/schemas/auth.py`, `alembic/versions/002_*.py`, y tests.
- **Dependencias nuevas**: `pyotp` (TOTP). `argon2-cffi` y `python-jose` ya están declaradas.
- **Migraciones**: introduce migración 002; renumera las posteriores del roadmap (RBAC→003, etc.).
- **`usuarios` es mínima a propósito**: C-07 la extiende (ALTER) con PII de negocio (dni, cuil, cbu, legajo…) y agrega `asignacion`. El claim `roles` del JWT va vacío hasta que C-04 (catálogo) + C-07 (asignaciones) lo pueblen.
- **Habilita**: C-04 (RBAC, usa `get_current_user`) y todo endpoint autenticado del sistema.
- **Governance**: CRÍTICO — autenticación y credenciales. Requiere aprobación humana y tests de seguridad obligatorios (identidad inmutable, rotación, un solo uso).
