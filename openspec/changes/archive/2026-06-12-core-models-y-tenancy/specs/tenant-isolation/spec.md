## ADDED Requirements

### Requirement: Repository genérico con scope de tenant por defecto

El sistema SHALL proveer un repository genérico base que se construya siempre con un `tenant_id` de contexto y aplique el scope `tenant_id` en TODAS sus consultas por defecto. NO SHALL existir una vía en la API del repository para ejecutar una consulta de dominio sin scope de tenant de forma accidental. Al persistir una entidad, el repository SHALL fijar su `tenant_id` desde el contexto del repository, ignorando cualquier `tenant_id` provisto en el dato de entrada.

#### Scenario: Lectura aislada por tenant

- **GIVEN** una entidad creada bajo el tenant A
- **WHEN** un repository construido con el `tenant_id` del tenant B intenta obtenerla por su `id`
- **THEN** el repository devuelve vacío (no expone datos del tenant A)

#### Scenario: Listado scoped

- **GIVEN** entidades de los tenants A y B en la misma tabla
- **WHEN** se lista mediante un repository construido con el `tenant_id` del tenant A
- **THEN** solo se devuelven las entidades del tenant A

#### Scenario: Alta fija el tenant del contexto

- **WHEN** se agrega una entidad mediante el repository de un tenant
- **THEN** la entidad persiste con el `tenant_id` del repository, aunque el objeto entrante traiga otro `tenant_id`

### Requirement: Soft delete transversal

El sistema SHALL implementar borrado lógico: las entidades se marcan con `deleted_at` y NUNCA se eliminan físicamente. El repository base SHALL excluir las entidades con `deleted_at` no nulo en sus consultas por defecto, y SHALL ofrecer un método explícito y nombrado para incluir borrados cuando un caso de auditoría lo requiera.

#### Scenario: Borrado lógico, no físico

- **WHEN** se elimina una entidad mediante el repository
- **THEN** la fila permanece en la tabla con `deleted_at` poblado
- **AND** no se ejecuta un DELETE físico

#### Scenario: Borrados excluidos por defecto

- **GIVEN** una entidad con `deleted_at` poblado
- **WHEN** se la busca o lista con los métodos por defecto del repository
- **THEN** no aparece en los resultados

#### Scenario: Acceso explícito a borrados

- **GIVEN** una entidad soft-deleted del tenant
- **WHEN** se la consulta mediante el método explícito que incluye borrados
- **THEN** la entidad es recuperable para fines de auditoría
