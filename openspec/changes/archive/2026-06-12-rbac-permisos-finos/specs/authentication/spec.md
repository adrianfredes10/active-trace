## MODIFIED Requirements

### Requirement: Emisión de JWT con claims mínimos

El sistema SHALL emitir un access token JWT firmado de vida corta (15 minutos) cuyos claims SHALL limitarse a `sub` (user id), `tenant_id`, `roles`, `exp` y `type`. El claim `roles` SHALL poblarse con los códigos de rol vigentes del usuario resueltos desde `usuario_rol` dentro de su tenant. El token NO SHALL contener permisos. Los permisos SHALL resolverse server-side en cada petición a partir de los roles.

#### Scenario: Claims del access token

- **WHEN** se emite un access token tras un login válido
- **THEN** el token contiene `sub`, `tenant_id`, `roles`, `exp` y `type=access`
- **AND** no contiene la lista de permisos del usuario

#### Scenario: Roles poblados desde usuario_rol

- **GIVEN** un usuario con uno o más roles asignados en `usuario_rol` dentro de su tenant
- **WHEN** se emite su access token tras un login válido
- **THEN** el claim `roles` contiene los códigos de esos roles
- **AND** un usuario sin roles asignados recibe `roles` vacío
