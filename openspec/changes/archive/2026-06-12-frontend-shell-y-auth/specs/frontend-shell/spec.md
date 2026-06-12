## ADDED Requirements

### Requirement: Cliente HTTP con refresh transparente

El frontend SHALL centralizar las llamadas HTTP en `@/shared/services/api` con interceptor que adjunta el access token y, ante 401 recuperable, renueva la sesión vía `POST /api/auth/refresh` sin intervención del usuario.

#### Scenario: Reintento tras refresh exitoso

- **GIVEN** una sesión con refresh token válido y access token expirado
- **WHEN** una request autenticada recibe 401
- **THEN** el cliente renueva tokens y reintenta la request original una vez

#### Scenario: Refresh fallido

- **GIVEN** refresh token inválido o revocado
- **WHEN** el interceptor no puede renovar
- **THEN** la sesión se limpia y el usuario es redirigido a login

### Requirement: Flujos de autenticación

El frontend SHALL exponer pantallas de login (tenant + email + password), verificación 2FA, recuperación y reset de contraseña consumiendo los endpoints de C-03.

#### Scenario: Login directo

- **WHEN** el usuario ingresa credenciales válidas sin 2FA
- **THEN** se almacena la sesión y navega al home

#### Scenario: Login con 2FA

- **WHEN** el backend responde `requires_2fa`
- **THEN** el usuario completa el código TOTP y obtiene tokens

### Requirement: Guards de ruta y permiso

El frontend SHALL proteger rutas autenticadas y permitir ocultar UI según permisos efectivos del backend.

#### Scenario: Sin sesión

- **WHEN** un usuario no autenticado accede a una ruta protegida
- **THEN** es redirigido a `/login`

#### Scenario: Sin permiso

- **GIVEN** un usuario autenticado sin el permiso requerido
- **WHEN** intenta ver un bloque protegido por `PermissionGate`
- **THEN** no se renderiza el contenido restringido

### Requirement: Layout adaptativo

El shell SHALL mostrar navegación basada en permisos efectivos (`GET /api/rbac/permisos-efectivos`) y un botón de logout.

#### Scenario: Menú según permisos

- **GIVEN** un usuario con `auditoria:ver`
- **WHEN** carga el layout autenticado
- **THEN** ve el ítem de navegación de auditoría
