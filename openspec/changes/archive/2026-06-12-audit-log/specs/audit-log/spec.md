## ADDED Requirements

### Requirement: Entidad AuditLog append-only

El sistema SHALL persistir entradas de auditor?a en `audit_logs` con campos: `tenant_id`, `fecha_hora`, `actor_id`, `impersonado_id` (opcional), `materia_id` (opcional), `accion`, `detalle` (JSONB), `filas_afectadas`, `ip`, `user_agent`. La tabla NO SHALL soportar UPDATE ni DELETE a nivel aplicaci?n ni base de datos.

#### Scenario: Inserci?n permitida

- **WHEN** se registra una acci?n v?lida v?a `AuditService.record()`
- **THEN** se crea una fila en `audit_logs` con el tenant del contexto

#### Scenario: Mutaci?n rechazada en DB

- **WHEN** se intenta UPDATE o DELETE sobre una fila de `audit_logs`
- **THEN** PostgreSQL rechaza la operaci?n con error

### Requirement: Cat?logo cerrado de c?digos de acci?n

El sistema SHALL aceptar solo c?digos definidos en `AuditAction` (RN-24). C?digos no catalogados SHALL ser rechazados al registrar.

#### Scenario: C?digo v?lido

- **WHEN** se registra con `accion=IMPERSONACION_INICIAR`
- **THEN** la entrada se persiste con ese c?digo

#### Scenario: C?digo inv?lido

- **WHEN** se intenta registrar con un c?digo arbitrario no catalogado
- **THEN** el servicio lanza error y no persiste la entrada

### Requirement: Atribuci?n bajo impersonaci?n

Cuando la sesi?n incluye impersonaci?n, cada entrada SHALL registrar `actor_id` como el usuario real (quien impersona) e `impersonado_id` como el usuario objetivo.

#### Scenario: Entrada con impersonaci?n activa

- **GIVEN** un ADMIN impersonando a un PROFESOR
- **WHEN** se registra una acci?n con `AuditContext.from_user(current_user)`
- **THEN** `actor_id` es el ADMIN e `impersonado_id` es el PROFESOR

### Requirement: Impersonaci?n controlada con auditor?a

El sistema SHALL exponer impersonaci?n solo a usuarios con permiso `impersonacion:usar`. Al iniciar o finalizar impersonaci?n SHALL registrarse `IMPERSONACION_INICIAR` o `IMPERSONACION_FINALIZAR` respectivamente.

#### Scenario: Inicio de impersonaci?n

- **GIVEN** un ADMIN con `impersonacion:usar`
- **WHEN** llama a `POST /api/auth/impersonate/start` con un usuario v?lido del mismo tenant
- **THEN** recibe un access token con claim `impersonated_sub`
- **AND** existe una entrada `IMPERSONACION_INICIAR` en el audit log

#### Scenario: Fin de impersonaci?n

- **GIVEN** una sesi?n con impersonaci?n activa
- **WHEN** llama a `POST /api/auth/impersonate/stop`
- **THEN** recibe un access token sin `impersonated_sub`
- **AND** existe una entrada `IMPERSONACION_FINALIZAR`

#### Scenario: Sin permiso

- **GIVEN** un usuario sin `impersonacion:usar`
- **WHEN** intenta iniciar impersonaci?n
- **THEN** la respuesta es 403

### Requirement: Consulta de audit log

El sistema SHALL exponer `GET /api/audit` protegido con `auditoria:ver`, retornando entradas del tenant del usuario autenticado.

#### Scenario: Usuario autorizado

- **GIVEN** un usuario con `auditoria:ver`
- **WHEN** consulta `GET /api/audit`
- **THEN** recibe la lista de entradas de su tenant

#### Scenario: Usuario sin permiso

- **GIVEN** un usuario sin `auditoria:ver`
- **WHEN** consulta `GET /api/audit`
- **THEN** la respuesta es 403
