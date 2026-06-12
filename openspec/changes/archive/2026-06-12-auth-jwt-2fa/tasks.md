## 1. Dependencias

- [x] 1.1 Declarar `pyotp` en `backend/pyproject.toml` (TOTP). Confirmar `argon2-cffi` y `python-jose[cryptography]` ya presentes.

## 2. Primitivas de seguridad (core/security.py)

- [x] 2.1 (RED) Tests Argon2id: `hash_password` produce hash != plaintext; `verify_password` ok con correcto, falla con incorrecto
- [x] 2.2 (GREEN) Implementar `hash_password`/`verify_password` (argon2-cffi, parámetros seguros por defecto)
- [x] 2.3 (RED) Tests JWT: `create_access_token` con claims mínimos; `decode_token` verifica firma/exp/type; token expirado o de tipo incorrecto falla
- [x] 2.4 (GREEN) Implementar `create_access_token`/`create_challenge_token`/`decode_token` (python-jose HS256, claims `sub`/`tenant_id`/`roles`/`exp`/`type`). Refresh resuelto como token opaco (`generate_opaque_token`+`hash_token`) por decisión D4, no JWT
- [x] 2.5 (RED) Tests blind index: determinista, normaliza (lower/trim), no contiene el valor
- [x] 2.6 (GREEN) Implementar `email_blind_index` (HMAC-SHA256 con pepper de `SECRET_KEY`)
- [x] 2.7 (RED) Tests TOTP: `verify_totp` acepta código válido del secreto, rechaza inválido
- [x] 2.8 (GREEN) Implementar `generate_totp_secret`/`totp_provisioning_uri`/`verify_totp` (pyotp)
- [x] 2.9 (REFACTOR) `core/security.py` queda en 202 LOC (<500); no requiere partición

## 3. Modelos y migración 002 (auth-storage)

- [x] 3.1 (RED) Tests de modelo: crear `Usuario` mínimo; unicidad `(tenant_id, email_hash)`; mismo email en otro tenant es válido
- [x] 3.2 (GREEN) Implementar `models/usuario.py` (auth-only, `TenantScopedMixin`): `email` (EncryptedString), `email_hash` (unique por tenant), `password_hash`, `is_active`, `two_factor_enabled`, `totp_secret` (EncryptedString nullable)
- [x] 3.3 (GREEN) Implementar `models/auth_token.py`: `RefreshToken` (token_hash, expires_at, revoked_at, replaced_by_id, usuario_id FK) y `PasswordResetToken` (token_hash, expires_at, used_at, usuario_id FK)
- [x] 3.4 (GREEN) Reexportar en `models/__init__.py`
- [x] 3.5 Generar `alembic/versions/002_create_auth_tables.py` (crea las 3 tablas, índice único `(tenant_id, email_hash)`)
- [x] 3.6 Verificar `alembic upgrade head` y `downgrade -1` contra la DB de test

## 4. Repositorios (tenant-scoped)

- [x] 4.1 (RED) Test: `usuario_repository.get_by_email_hash` solo encuentra dentro del tenant
- [x] 4.2 (GREEN) Implementar `repositories/usuario_repository.py` (extiende `BaseRepository`, lookup por email_hash)
- [x] 4.3 (GREEN) Implementar repos de `refresh_tokens` y `password_reset_tokens` (crear, buscar por hash, revocar, marcar usado) tenant-scoped

## 5. Servicio de auth (services/auth_service.py)

- [x] 5.1 (RED) Tests login: OK sin 2FA emite par; password incorrecto → error genérico; usuario inactivo → falla
- [x] 5.2 (GREEN) Implementar `login` (lookup por email_hash en tenant, verify_password, emisión de tokens o challenge si 2FA)
- [x] 5.3 (RED) Tests refresh: rotación emite nuevo par y revoca anterior; reuso de revocado invalida cadena
- [x] 5.4 (GREEN) Implementar `refresh` (rotación + detección de reuso) y `logout` (revoca activo)
- [x] 5.5 (RED) Tests 2FA: enroll genera secret; confirm con código válido activa; login con 2FA exige challenge; verify con código válido emite sesión
- [x] 5.6 (GREEN) Implementar `enroll_2fa`/`confirm_2fa`/`verify_2fa`
- [x] 5.7 (RED) Tests recuperación: forgot genera token (hash) y respuesta genérica; reset consume un solo uso; reuso/expirado falla
- [x] 5.8 (GREEN) Implementar `forgot_password`/`reset_password`

## 6. Dependency get_current_user (core/dependencies.py)

- [x] 6.1 (RED) Tests: sin token → 401; token válido resuelve identidad+tenant; token inválido → 401
- [x] 6.2 (GREEN) Implementar `get_current_user` (decode access token, deriva identidad+tenant del JWT) → `CurrentUser`
- [x] 6.3 (GREEN) Exponer `get_tenant` derivado en `core/tenancy.py` (reemplaza el placeholder)

## 7. Endpoints y schemas (api/v1/routers/auth.py, schemas/auth.py)

- [x] 7.1 (GREEN) Schemas Pydantic con `extra='forbid'`: `LoginRequest`, `TokenResponse`, `RefreshRequest`, `TwoFactorVerifyRequest`, `Enroll2FAResponse`, `ForgotPasswordRequest`, `ResetPasswordRequest`; respuestas sin password_hash/totp_secret
- [x] 7.2 (GREEN) Router `/api/auth`: `login`, `2fa/enroll`, `2fa/confirm`, `2fa/verify`, `refresh`, `logout`, `forgot-password`, `reset-password`; registrar en `main.py`
- [x] 7.3 (GREEN) Rate limiter 5/60s por IP+email en `login` (`RateLimiter` en proceso) → 429 al exceder
- [x] 7.4 (RED→GREEN) Tests de API (httpx, DB real): login e2e OK/KO, refresh rotation + reuso, 2FA flow, forgot/reset single-use, rate limit 429

## 8. Verificación y cierre

- [x] 8.1 Suite completa con cobertura (`pytest --cov=app`): 94% líneas total; reglas de auth ≥90% (auth_service 96%, security 100%)
- [x] 8.2 Confirmar ≤500 LOC por archivo (auth_service 204, security 202, router 189) y queries de dominio siempre con scope de tenant
- [x] 8.3 Marcar tasks y dejar listo para `/opsx:archive`
