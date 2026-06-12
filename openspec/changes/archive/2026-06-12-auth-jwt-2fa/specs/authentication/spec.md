## ADDED Requirements

### Requirement: Login con email y password

El sistema SHALL exponer `POST /api/auth/login` que reciba email y password. El password SHALL validarse contra un hash Argon2id almacenado. Ante credenciales inválidas o usuario inactivo, el sistema SHALL responder con un error genérico que NO revele si el email existe. El login SHALL ser una de las pocas operaciones accesibles sin sesión.

#### Scenario: Login exitoso sin 2FA

- **GIVEN** un usuario activo sin 2FA, con su password
- **WHEN** llama a `POST /api/auth/login` con email y password correctos
- **THEN** recibe un access token (vida corta) y un refresh token

#### Scenario: Password incorrecto

- **WHEN** se llama a login con un password que no coincide
- **THEN** la respuesta es 401 con un error genérico, sin emitir tokens

#### Scenario: Usuario inactivo

- **GIVEN** un usuario con `is_active = false`
- **WHEN** intenta loguear con credenciales correctas
- **THEN** la respuesta es 401 y no se emite sesión

### Requirement: Emisión de JWT con claims mínimos

El sistema SHALL emitir un access token JWT firmado de vida corta (15 minutos) cuyos claims SHALL limitarse a `sub` (user id), `tenant_id`, `roles`, `exp` y `type`. El token NO SHALL contener permisos. Los permisos SHALL resolverse server-side en cada petición.

#### Scenario: Claims del access token

- **WHEN** se emite un access token tras un login válido
- **THEN** el token contiene `sub`, `tenant_id`, `roles`, `exp` y `type=access`
- **AND** no contiene la lista de permisos del usuario

### Requirement: Refresh token con rotación y detección de reuso

El sistema SHALL exponer `POST /api/auth/refresh` que rote el refresh token: el refresh usado SHALL invalidarse y emitirse un par nuevo. El sistema SHALL almacenar únicamente el hash del refresh token, nunca su valor. El reuso de un refresh ya revocado SHALL invalidar toda la cadena de refresh del usuario y responder 401.

#### Scenario: Rotación normal

- **GIVEN** un refresh token válido
- **WHEN** se llama a `POST /api/auth/refresh`
- **THEN** se emite un nuevo par access+refresh
- **AND** el refresh anterior queda revocado

#### Scenario: Reuso de refresh revocado

- **GIVEN** un refresh token que ya fue usado/rotado (revocado)
- **WHEN** se intenta usar nuevamente
- **THEN** la respuesta es 401
- **AND** toda la cadena de refresh del usuario queda invalidada

### Requirement: Logout revoca la sesión

El sistema SHALL exponer `POST /api/auth/logout` que revoque el refresh token activo de la sesión.

#### Scenario: Logout

- **GIVEN** una sesión con un refresh válido
- **WHEN** se llama a `POST /api/auth/logout`
- **THEN** el refresh queda revocado y no puede usarse para rotar

### Requirement: Identidad y tenant exclusivamente desde el token

El sistema SHALL resolver la identidad, el tenant y los roles del usuario autenticado EXCLUSIVAMENTE desde el JWT verificado server-side, mediante una dependency (`get_current_user`). Ningún dato de la petición (parámetro de URL, body, header) SHALL alterar o reemplazar la identidad del actor. Sin token válido, o con usuario inactivo, el acceso SHALL denegarse (fail-closed, 401).

#### Scenario: Acceso sin token

- **WHEN** se llama a un endpoint protegido sin `Authorization: Bearer`
- **THEN** la respuesta es 401

#### Scenario: Identidad inmutable por parámetro

- **GIVEN** una sesión autenticada del usuario U en el tenant T
- **WHEN** la petición incluye un `user_id` o `tenant_id` distinto en el path, query o body
- **THEN** la identidad efectiva sigue siendo U y el tenant sigue siendo T (los del token)

### Requirement: Rate limiting en login

El sistema SHALL limitar los intentos de login a 5 por 60 segundos por combinación de IP y email. Al exceder el límite, SHALL responder 429.

#### Scenario: Exceso de intentos

- **WHEN** se hacen 6 intentos de login en menos de 60 segundos desde la misma IP para el mismo email
- **THEN** el sexto intento responde 429
