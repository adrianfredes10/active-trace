## ADDED Requirements

### Requirement: Solicitud de recuperación de contraseña

El sistema SHALL exponer `POST /api/auth/forgot` que, dado un email, genere un token de recuperación de un solo uso con expiración corta, almacenando únicamente su hash. La respuesta SHALL ser genérica e idéntica exista o no el email (no revela cuentas). El login y la recuperación SHALL ser accesibles sin sesión.

#### Scenario: Solicitud para email existente

- **GIVEN** un usuario registrado
- **WHEN** llama a `POST /api/auth/forgot` con su email
- **THEN** se genera y persiste (hasheado) un token de un solo uso con expiración corta
- **AND** la respuesta es genérica (200) sin revelar si el email existe

#### Scenario: Solicitud para email inexistente

- **WHEN** se llama a `POST /api/auth/forgot` con un email no registrado
- **THEN** la respuesta es genérica e indistinguible del caso anterior

### Requirement: Reset de contraseña con token de un solo uso

El sistema SHALL exponer `POST /api/auth/reset` que reciba el token de recuperación y un nuevo password. El token SHALL aceptarse solo si no expiró y no fue usado. Tras un reset exitoso, el token SHALL marcarse como usado y no SHALL volver a aceptarse. El nuevo password SHALL almacenarse hasheado con Argon2id.

#### Scenario: Reset exitoso

- **GIVEN** un token de recuperación válido y vigente
- **WHEN** se llama a `POST /api/auth/reset` con el token y un nuevo password
- **THEN** el password se actualiza (hash Argon2id) y el token queda marcado como usado

#### Scenario: Reuso del token

- **GIVEN** un token ya usado en un reset exitoso
- **WHEN** se intenta usar nuevamente
- **THEN** la respuesta es un error y el password no cambia

#### Scenario: Token expirado

- **GIVEN** un token de recuperación cuya expiración ya pasó
- **WHEN** se intenta usar
- **THEN** la respuesta es un error y el password no cambia
