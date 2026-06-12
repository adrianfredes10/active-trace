## ADDED Requirements

### Requirement: Tabla de usuarios mínima para autenticación

El sistema SHALL persistir una tabla `usuarios` (tenant-scoped, heredando el mixin base) con los campos mínimos para autenticación: `email` (cifrado en reposo), `email_hash` (blind index para lookup, único por tenant), `password_hash` (Argon2id), `is_active`, `two_factor_enabled` y `totp_secret` (cifrado, nullable). Esta tabla SHALL ser extensible: cambios posteriores podrán agregar atributos de negocio sin recrearla.

#### Scenario: Unicidad de email por tenant

- **GIVEN** un usuario con cierto email en el tenant A
- **WHEN** se intenta crear otro usuario con el mismo email en el tenant A
- **THEN** la operación falla por unicidad del blind index dentro del tenant

#### Scenario: Mismo email en distintos tenants

- **GIVEN** un usuario con cierto email en el tenant A
- **WHEN** se crea un usuario con el mismo email en el tenant B
- **THEN** la operación es válida (la unicidad es por tenant)

### Requirement: Almacenamiento de refresh tokens

El sistema SHALL persistir los refresh tokens en una tabla `refresh_tokens` guardando el hash del token (nunca el valor), su expiración, su estado de revocación y la referencia al token que lo reemplaza (cadena de rotación).

#### Scenario: Persistencia del hash, no del valor

- **WHEN** se emite un refresh token
- **THEN** la base almacena su hash y nunca el valor en claro

### Requirement: Almacenamiento de tokens de recuperación

El sistema SHALL persistir los tokens de recuperación en una tabla `password_reset_tokens` guardando el hash del token, su expiración y su marca de uso (un solo uso).

#### Scenario: Token de reset de un solo uso

- **GIVEN** un token de recuperación emitido
- **WHEN** se consume en un reset exitoso
- **THEN** queda marcado como usado y no puede reutilizarse

### Requirement: Migración de las tablas de autenticación

El sistema SHALL incluir una migración Alembic que cree `usuarios`, `refresh_tokens` y `password_reset_tokens`, encadenada sobre la migración de `tenants`. La migración SHALL ser reversible.

#### Scenario: Upgrade crea las tablas de auth

- **WHEN** se aplica la migración sobre una base con la tabla `tenants`
- **THEN** existen `usuarios`, `refresh_tokens` y `password_reset_tokens` con sus columnas e índices

#### Scenario: Downgrade revierte

- **WHEN** se revierte la migración
- **THEN** las tres tablas dejan de existir
