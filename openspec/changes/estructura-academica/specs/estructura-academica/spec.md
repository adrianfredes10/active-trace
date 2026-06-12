# estructura-academica

## ADDED Requirements

### Requirement: Catálogo académico tenant-scoped

The system SHALL persist `Carrera`, `Cohorte` and `Materia` entities scoped by `tenant_id` with soft delete.

#### Scenario: Unicidad de carrera por tenant

- **WHEN** an admin creates two carreras with the same `codigo` in one tenant
- **THEN** the second creation is rejected

#### Scenario: Unicidad de materia por tenant

- **WHEN** an admin creates two materias with the same `codigo` in one tenant
- **THEN** the second creation is rejected

#### Scenario: Unicidad de cohorte por carrera

- **WHEN** an admin creates two cohortes with the same `nombre` for the same `carrera_id`
- **THEN** the second creation is rejected

### Requirement: Cohorte pertenece a una carrera

Each `Cohorte` SHALL reference exactly one `Carrera` via mandatory `carrera_id`.

#### Scenario: Alta de cohorte

- **WHEN** an admin creates a cohorte with a valid active carrera
- **THEN** the cohorte is persisted with the given `carrera_id`

### Requirement: Carrera inactiva bloquea cohortes nuevas

A carrera in `Inactiva` state SHALL NOT accept new cohortes.

#### Scenario: Rechazo por carrera inactiva

- **WHEN** an admin attempts to create a cohorte for an inactive carrera
- **THEN** the request is rejected with a business error

### Requirement: ABM protegido por RBAC

Admin endpoints `/api/admin/carreras`, `/api/admin/cohortes` and `/api/admin/materias` SHALL require permission `estructura:gestionar`.

#### Scenario: Sin permiso

- **WHEN** a user without `estructura:gestionar` calls any admin estructura endpoint
- **THEN** the response is HTTP 403
