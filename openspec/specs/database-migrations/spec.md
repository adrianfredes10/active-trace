# database-migrations Specification

## Purpose

Gestionar la evolución del schema de base de datos con Alembic, comenzando por la migración 001 que crea la tabla `tenants`, bajo la convención de una migración por cambio de schema.

## Requirements

### Requirement: Migración inicial de la tabla tenants

El sistema SHALL incluir una migración Alembic (001) que cree la tabla `tenants` con sus columnas (`id`, `nombre`, `slug`, `estado`, `created_at`, `updated_at`, `deleted_at`) y la restricción de unicidad sobre `slug`. La migración SHALL ser reversible (downgrade elimina la tabla).

#### Scenario: Upgrade crea la tabla

- **WHEN** se aplica la migración 001 sobre una base vacía
- **THEN** la tabla `tenants` existe con todas sus columnas e índices

#### Scenario: Downgrade revierte

- **WHEN** se revierte la migración 001
- **THEN** la tabla `tenants` deja de existir

### Requirement: Convención de una migración por cambio de schema

El sistema SHALL adoptar la convención de una migración Alembic por cada cambio de schema. Cada cambio que altere la estructura de la base de datos SHALL aportar su propia migración encadenada sobre la anterior.

#### Scenario: Cadena de migraciones consistente

- **WHEN** se inspecciona el historial de migraciones
- **THEN** cada migración referencia a su predecesora formando una cadena lineal sin huérfanas
