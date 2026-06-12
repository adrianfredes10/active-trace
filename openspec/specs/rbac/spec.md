# rbac Specification

## Purpose
TBD - created by archiving change rbac-permisos-finos. Update Purpose after archive.
## Requirements
### Requirement: Catálogo administrable rol × permiso

El sistema SHALL modelar la autorización como datos: tablas `rol`, `permiso` (`modulo:accion`) y la matriz `rol_permiso`, todas acotadas por tenant. La matriz NO SHALL estar hardcodeada en el código. El sistema SHALL sembrar de forma idempotente los roles del dominio (ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS) y la matriz de capacidades base por tenant.

#### Scenario: Roles del dominio sembrados

- **GIVEN** un tenant recién inicializado
- **WHEN** se ejecuta el seed de RBAC
- **THEN** existen los 7 roles del dominio en ese tenant
- **AND** el rol ADMIN tiene asociados sus permisos de la matriz base

#### Scenario: Seed idempotente

- **WHEN** el seed de RBAC se ejecuta dos veces sobre el mismo tenant
- **THEN** no se duplican roles, permisos ni filas de la matriz

### Requirement: Link usuario↔rol a nivel tenant

El sistema SHALL permitir asociar uno o más roles a un usuario mediante `usuario_rol`, acotado por tenant. Un usuario SHALL poder tener múltiples roles. Esta asociación es a nivel tenant (sin contexto académico ni vigencia en esta capability).

#### Scenario: Usuario con múltiples roles

- **GIVEN** un usuario en un tenant
- **WHEN** se le asignan los roles PROFESOR y COORDINADOR
- **THEN** ambos roles quedan asociados al usuario dentro de ese tenant

### Requirement: Resolución de permisos efectivos server-side

El sistema SHALL resolver los permisos efectivos de un usuario por petición como la unión de los permisos de sus roles (claim `roles` del JWT), acotada a su tenant, leída desde `rol_permiso`. Los permisos NO SHALL almacenarse en el token.

#### Scenario: Unión de permisos de varios roles

- **GIVEN** un usuario con dos roles cuya matriz define permisos distintos
- **WHEN** se resuelven sus permisos efectivos
- **THEN** obtiene la unión de los permisos de ambos roles
- **AND** la resolución solo considera datos de su propio tenant

### Requirement: Guard require_permission fail-closed

El sistema SHALL exponer un guard `require_permission("modulo:accion")` que cada endpoint protegido declara. Si el usuario autenticado NO posee el permiso requerido, el sistema SHALL responder 403. La ausencia de un permiso explícito SHALL denegar el acceso (fail-closed). NO SHALL existir un flag binario de superusuario.

#### Scenario: Usuario sin permiso

- **GIVEN** un usuario autenticado cuyo conjunto de permisos no incluye `calificaciones:importar`
- **WHEN** llama a un endpoint protegido con `require_permission("calificaciones:importar")`
- **THEN** la respuesta es 403

#### Scenario: Usuario con permiso

- **GIVEN** un usuario cuyo rol incluye `calificaciones:importar`
- **WHEN** llama al endpoint protegido por ese permiso
- **THEN** el acceso se concede y el endpoint ejecuta

