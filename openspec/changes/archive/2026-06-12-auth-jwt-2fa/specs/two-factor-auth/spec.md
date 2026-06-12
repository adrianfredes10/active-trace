## ADDED Requirements

### Requirement: Enrolamiento de 2FA TOTP

El sistema SHALL permitir a un usuario autenticado enrolar un segundo factor TOTP mediante `POST /api/auth/2fa/enroll`, que genere un secreto TOTP (almacenado cifrado) y devuelva la información necesaria para configurarlo (URI de aprovisionamiento). El 2FA SHALL activarse solo tras confirmar un código válido mediante `POST /api/auth/2fa/confirm`.

#### Scenario: Enrolar y activar 2FA

- **GIVEN** un usuario autenticado sin 2FA
- **WHEN** llama a `POST /api/auth/2fa/enroll`
- **THEN** recibe un URI de aprovisionamiento y se almacena el secreto cifrado
- **AND** al confirmar con un código TOTP válido vía `POST /api/auth/2fa/confirm`, queda `two_factor_enabled = true`

#### Scenario: Confirmación con código inválido

- **GIVEN** un usuario que enroló pero no confirmó 2FA
- **WHEN** confirma con un código TOTP incorrecto
- **THEN** la respuesta es un error y `two_factor_enabled` permanece `false`

### Requirement: Gate de 2FA entre credenciales y sesión

Cuando un usuario tiene 2FA activo, el sistema SHALL exigir el segundo factor entre la validación de credenciales y la emisión de la sesión. Tras validar email+password, SHALL emitir un challenge de vida corta y NO emitir access/refresh hasta verificar un código TOTP válido mediante `POST /api/auth/2fa/verify`.

#### Scenario: Login con 2FA requiere segundo factor

- **GIVEN** un usuario con `two_factor_enabled = true`
- **WHEN** hace login con credenciales correctas
- **THEN** recibe un challenge (no un access token) indicando que se requiere 2FA

#### Scenario: Verificación del segundo factor

- **GIVEN** un challenge válido emitido tras validar credenciales
- **WHEN** se llama a `POST /api/auth/2fa/verify` con el challenge y un código TOTP válido
- **THEN** se emite el par access+refresh

#### Scenario: Código TOTP inválido en verificación

- **GIVEN** un challenge válido
- **WHEN** se verifica con un código TOTP incorrecto
- **THEN** la respuesta es 401 y no se emite sesión
