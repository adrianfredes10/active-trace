## ADDED Requirements

### Requirement: Entidad Tenant raíz

El sistema SHALL definir una entidad `Tenant` como raíz del modelo multi-tenant, persistida en la tabla `tenants`. `Tenant` SHALL tener `id` (UUID), `nombre`, `slug` (único global), `estado` (Activo|Inactivo) y los campos de timestamp y soft delete. `Tenant` NO SHALL llevar columna `tenant_id` (es la raíz del aislamiento, no un sujeto de él).

#### Scenario: Crear un tenant

- **WHEN** se persiste un `Tenant` con `nombre` y `slug` válidos
- **THEN** se almacena con un `id` UUID generado, `estado` por defecto `Activo` y timestamps poblados

#### Scenario: Slug único

- **WHEN** se intenta persistir un segundo `Tenant` con un `slug` ya existente
- **THEN** la operación falla por violación de unicidad

### Requirement: Mixin base de entidad

El sistema SHALL proveer un mixin base que toda entidad de dominio herede, aportando `id` (UUID v4 generado por la aplicación), `created_at` (poblado en la inserción), `updated_at` (actualizado automáticamente en cada modificación) y `deleted_at` (nullable, para soft delete). Las entidades con scope de tenant SHALL heredar además la columna `tenant_id` (FK → `tenants.id`, indexada, no nula).

#### Scenario: Timestamps automáticos en alta

- **WHEN** se inserta una entidad que usa el mixin base
- **THEN** `created_at` y `updated_at` quedan poblados con la marca temporal del alta
- **AND** `deleted_at` queda nulo

#### Scenario: updated_at se actualiza al modificar

- **WHEN** se modifica y persiste una entidad existente
- **THEN** `updated_at` refleja una marca temporal posterior a la del alta
- **AND** `created_at` permanece sin cambios

#### Scenario: Identidad por UUID

- **WHEN** se crea cualquier entidad de dominio
- **THEN** su identidad es un `id` UUID interno opaco, independiente de cualquier atributo de negocio (p. ej. legajo)
