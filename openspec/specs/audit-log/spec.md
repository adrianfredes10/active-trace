# audit-log Specification

## Purpose

Registro append-only de acciones significativas (E-AUD) con catálogo cerrado de códigos, atribución correcta bajo impersonación, y API de lectura tenant-scoped.

## Requirements

### Requirement: Entidad AuditLog append-only

El sistema SHALL persistir entradas de auditoría en `audit_logs` con campos: `tenant_id`, `fecha_hora`, `actor_id`, `impersonado_id` (opcional), `materia_id` (opcional), `accion`, `detalle` (JSONB), `filas_afectadas`, `ip`, `user_agent`. La tabla NO SHALL soportar UPDATE ni DELETE a nivel aplicación ni base de datos.

#### Scenario: Inserción permitida

- **WHEN** se registra una acción válida vía `AuditService.record()`
- **THEN** se crea una fila en `audit_logs` con el tenant del contexto

#### Scenario: Mutación rechazada en DB

- **WHEN** se intenta UPDATE o DELETE sobre una fila de `audit_logs`
- **THEN** PostgreSQL rechaza la operación con error

### Requirement: Catálogo cerrado de códigos de acción

El sistema SHALL aceptar solo códigos definidos en `AuditAction` (RN-24). Códigos no catalogados SHALL ser rechazados al registrar.

#### Scenario: Código válido

- **WHEN** se registra con `accion=IMPERSONACION_INICIAR`
- **THEN** la entrada se persiste con ese código

#### Scenario: Código inválido

- **WHEN** se intenta registrar con un código arbitrario no catalogado
- **THEN** el servicio lanza error y no persiste la entrada

### Requirement: Atribución bajo impersonación

Cuando la sesión incluye impersonación, cada entrada SHALL registrar `actor_id` como el usuario real (quien impersona) e `impersonado_id` como el usuario objetivo.

#### Scenario: Entrada con impersonación activa

- **GIVEN** un ADMIN impersonando a un PROFESOR
- **WHEN** se registra una acción con `AuditContext.from_user(current_user)`
- **THEN** `actor_id` es el ADMIN e `impersonado_id` es el PROFESOR

### Requirement: Impersonación controlada con auditoría

El sistema SHALL exponer impersonación solo a usuarios con permiso `impersonacion:usar`. Al iniciar o finalizar impersonación SHALL registrarse `IMPERSONACION_INICIAR` o `IMPERSONACION_FINALIZAR` respectivamente.

#### Scenario: Inicio de impersonación

- **GIVEN** un ADMIN con `impersonacion:usar`
- **WHEN** llama a `POST /api/auth/impersonate/start` con un usuario válido del mismo tenant
- **THEN** recibe un access token con claim `impersonated_sub`
- **AND** existe una entrada `IMPERSONACION_INICIAR` en el audit log

#### Scenario: Fin de impersonación

- **GIVEN** una sesión con impersonación activa
- **WHEN** llama a `POST /api/auth/impersonate/stop`
- **THEN** recibe un access token sin `impersonated_sub`
- **AND** existe una entrada `IMPERSONACION_FINALIZAR`

#### Scenario: Sin permiso

- **GIVEN** un usuario sin `impersonacion:usar`
- **WHEN** intenta iniciar impersonación
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
