## Context

C-03 implementa la autenticación propia (ADR-001: auth propio, no IdP externo — `docs/ARQUITECTURA.md §5.1`). Contrato cerrado: password **Argon2id**, sesión = **JWT firmado** access 15 min + **refresh con rotación**, claims mínimos `sub`/`tenant_id`/`roles`/`exp`, **2FA TOTP opcional**, recuperación con **token de un solo uso**, **regla de oro de identidad** (FL-01, `03 §1`), rate limiting login (RNF-11). C-02 dejó el cimiento: mixins, repo tenant-scoped, cifrado AES-256, slot `core/security.py` (cifrado ya implementado), slots `core/dependencies.py` y `core/tenancy.py`.

Governance **CRÍTICO**. TDD estricto; los tests de seguridad (identidad inmutable, rotación, single-use) son la red principal.

## Goals / Non-Goals

**Goals:**

- Tabla `usuarios` mínima (auth-only) + `refresh_tokens` + `password_reset_tokens` (migración 002).
- Argon2id, JWT (access+refresh), blind index de email, TOTP — en `core/security.py`.
- `get_current_user`: identidad + tenant SOLO del token verificado (fail-closed).
- Endpoints `/api/auth`: login, 2FA, refresh (rotación + detección de reuso), logout, forgot, reset.
- Rate limiting 5/60s por IP+email en login.
- Tests DB real: login OK/KO, rotación + reuso, 2FA, single-use reset, rate limit, identidad inmutable.

**Non-Goals:**

- Entidad `Usuario` completa (PII de negocio, legajo, etc.) y `Asignacion` → C-07 (ALTER + nueva tabla).
- Catálogo de roles/permisos y `require_permission` → C-04. El claim `roles` va `[]` hasta entonces.
- Envío real del email de reset (SMTP/N8N) → integración posterior; C-03 persiste el token y expone el flujo.
- Impersonación (`impersonacion:usar`) → change de auditoría/RBAC posterior.

## Decisions

### D1 — Tabla `usuarios` mínima ahora, extendida por C-07

C-03 crea `usuarios` solo con lo que auth necesita, heredando `TenantScopedMixin` (C-02):

| Columna | Tipo | Notas |
|---------|------|-------|
| `email` | `EncryptedString` | cifrado AES-256 (PII) |
| `email_hash` | `String` | blind index determinista; único `(tenant_id, email_hash)` |
| `password_hash` | `String` | Argon2id |
| `is_active` | `bool` | default `True`; inactivo no puede loguear |
| `two_factor_enabled` | `bool` | default `False` |
| `totp_secret` | `EncryptedString` nullable | cifrado; presente solo si enroló 2FA |

C-07 hará `ALTER usuarios` para sumar `nombre`, `apellidos`, `dni`, `cuil`, `cbu`, `alias_cbu`, `legajo`, etc., y creará `asignacion`. **No** duplicamos la tabla: una sola `usuarios` que crece.

### D2 — Blind index para login sobre email cifrado

GCM es no determinista → no se puede `WHERE email = :x`. Para buscar al usuario por el email que tipea: `email_hash = HMAC_SHA256(pepper, normalize(email))` con `normalize` = lower+trim, y `pepper` derivado de `SECRET_KEY`. El `email_hash` es determinista (permite igualdad e índice único) pero no reversible. El `email` cifrado se conserva para mostrar/reset. **Trade-off**: HMAC con pepper fijo permite igualdad pero no "contains"; suficiente para auth. Rotar `SECRET_KEY` invalidaría los hashes (operación de despliegue, documentada).

### D3 — `core/security.py`: una sola casa para crypto

Amplía el módulo de C-02 (que ya tiene AES-256). Agrega:

- **Argon2id**: `hash_password` / `verify_password` (argon2-cffi, parámetros por defecto seguros). `verify_password` re-hashea si los parámetros quedaron viejos (opcional, no bloqueante).
- **JWT** (python-jose, HS256 con `SECRET_KEY`): `create_access_token(sub, tenant_id, roles, ttl=15min)`, `create_refresh_token(...)`, `create_challenge_token(...)` (2FA, TTL muy corto), `decode_token(token) -> claims` (verifica firma + exp + `type`). Claims: `sub`, `tenant_id`, `roles`, `exp`, `type` ∈ {access, refresh, challenge}.
- **Blind index**: `email_blind_index(email)`.
- **TOTP** (pyotp): `generate_totp_secret`, `totp_provisioning_uri`, `verify_totp(secret, code)`.

Si el archivo se acerca a 500 LOC, se parte por responsabilidad (`security/passwords.py`, `security/tokens.py`, …); se evalúa en implementación.

### D4 — Refresh con rotación + detección de reuso

`refresh_tokens`: `token_hash` (solo hash, nunca el valor), `expires_at`, `revoked_at`, `replaced_by_id`. Flujo:

- En login se emite refresh: se guarda su hash.
- En `/refresh`: se valida el hash, se verifica no revocado/no vencido, se **revoca** (set `revoked_at` + `replaced_by_id`) y se emite uno nuevo.
- **Reuso de un refresh ya revocado** = señal de robo → se **revoca toda la cadena** del usuario y se responde 401. (Patrón refresh token rotation con reuse detection.)
- `/logout` revoca el refresh activo.

El refresh se entrega al cliente como token opaco firmado; el server solo guarda su hash (SHA-256), igual criterio que reset.

### D5 — Gate 2FA entre credenciales y sesión (FL-01 variante)

`/login`:
1. Rate limit (D6). Lookup por `email_hash` dentro del tenant. (Resolución de tenant: ver D7.)
2. `verify_password`. Si falla → 401 genérico (no revela si el email existe).
3. Si `two_factor_enabled` → emite **challenge token** (TTL ~5 min, `type=challenge`) y responde "2FA requerido". El cliente llama `/2fa/verify` con el challenge + código TOTP → si OK, emite access+refresh.
4. Si no → emite access+refresh directo.

Enrolamiento: `/2fa/enroll` (autenticado) genera secret + provisioning URI (QR); `/2fa/confirm` valida un código y activa `two_factor_enabled`.

### D6 — Rate limiting login 5/60s por IP+email

Limiter de ventana deslizante **en proceso** (dict con timestamps), clave `(ip, email_hash)`. Al exceder → 429. **Limitación conocida**: no es compartido entre instancias; para producción multi-instancia se reemplaza por un store compartido (Redis) detrás de la misma interfaz. Se deja la interfaz `RateLimiter` para no acoplar. No se mete Redis al stack en C-03.

### D7 — Resolución de tenant en login (sin sesión previa)

Login es anónimo: todavía no hay JWT que indique el tenant. Opciones de resolución del tenant en login (a confirmar en implementación, no bloquea el diseño): (a) subdominio/`slug` del tenant en el host, (b) `email_hash` único global con índice que incluye tenant, (c) header `X-Tenant-Slug`. Para C-03 se asume **slug de tenant explícito en el request de login** (campo `tenant_slug` o host), resuelto contra la tabla `tenants` (C-02). Una vez autenticado, el `tenant_id` viaja SIEMPRE en el JWT y jamás se vuelve a tomar del request (regla de oro). Esto NO viola la regla: en login el usuario aún no tiene sesión; el tenant_slug es dato de entrada para localizar la cuenta, y las credenciales validan la pertenencia.

### D8 — `get_current_user`: identidad solo del token

Dependency que: extrae `Authorization: Bearer`, `decode_token`, exige `type=access`, carga el usuario por `sub` **dentro del `tenant_id` del token** (vía repo tenant-scoped), valida `is_active`. Devuelve un `CurrentUser` (user_id, tenant_id, roles). Sin token / inválido / inactivo → 401. **Ningún** `user_id`/`tenant_id` del path/body/query altera esto. `core/tenancy.py` (slot C-03) puede exponer `get_tenant` derivado de `get_current_user`.

### D9 — Schemas Pydantic `extra='forbid'`

Todos los DTO de `/api/auth` (`LoginRequest`, `TokenPair`, `RefreshRequest`, `TwoFactorVerifyRequest`, `EnrollResponse`, `ForgotRequest`, `ResetRequest`) con `ConfigDict(extra='forbid')`. Las respuestas NUNCA incluyen `password_hash`, `totp_secret` ni el email en claro innecesariamente.

## Risks / Trade-offs

- **[Rate limiter en proceso no escala horizontalmente]** → Aceptado para C-03 con interfaz desacoplada; Redis en producción multi-instancia.
- **[Blind index permite enumeración por igualdad si se filtra el pepper]** → El pepper vive en `SECRET_KEY` (secreto). Respuestas de login/forgot son genéricas (no revelan existencia del email).
- **[Renumerar migraciones del roadmap]** → C-03 toma 002; documentado en el proposal. Las migraciones reales se encadenan por `down_revision`, no por el número del roadmap.
- **[Claim `roles` vacío hasta C-04/C-07]** → `get_current_user` devuelve `roles=[]`; los endpoints que exijan permisos (C-04) fallarán closed hasta que el RBAC esté. Correcto y seguro.
- **[Tenant en login]** → D7 asume slug explícito; si el modelo de despliegue (subdominio) difiere, se ajusta sin tocar el resto (la regla de oro sigue intacta post-login).
- **[Envío de email de reset fuera de scope]** → C-03 deja el token persistido y el endpoint; el canal de envío se integra después. Riesgo: sin envío, el reset no es usable e2e hasta esa integración (aceptado, es infra).

## Migration Plan

`Migración 002` crea `usuarios`, `refresh_tokens`, `password_reset_tokens` (encadenada sobre 001). Reversible. C-07 agregará `ALTER usuarios` + `asignacion` en su propia migración. Sin datos productivos aún.

## Open Questions

- **Resolución de tenant en login (D7)**: ¿slug explícito, subdominio o header? Se cierra en implementación según el modelo de despliegue; no bloquea el diseño.
- **Partición de `core/security.py`**: si supera 500 LOC, se parte por responsabilidad. Decisión de implementación.
- **Re-hash de password con parámetros nuevos**: opcional; se evalúa en implementación.
