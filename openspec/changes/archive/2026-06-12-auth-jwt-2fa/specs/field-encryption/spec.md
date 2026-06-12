## ADDED Requirements

### Requirement: Blind index determinista para lookup sobre datos cifrados

El sistema SHALL proveer un blind index determinista (HMAC-SHA256 con un pepper derivado de la configuración) para permitir búsquedas por igualdad sobre atributos cifrados (caso: login por email, que está cifrado en reposo). El blind index SHALL normalizar la entrada (minúsculas, sin espacios) antes de calcular el HMAC, SHALL ser determinista para permitir índices únicos, y NO SHALL ser reversible al valor original.

#### Scenario: Mismo valor produce el mismo índice

- **WHEN** se calcula el blind index del mismo email dos veces (con distinta capitalización o espacios)
- **THEN** ambos resultados son idénticos (entrada normalizada)

#### Scenario: El blind index no revela el valor

- **WHEN** se calcula el blind index de un email
- **THEN** el resultado no contiene el email en claro ni permite recuperarlo

#### Scenario: Lookup por igualdad

- **GIVEN** un usuario almacenado con su email cifrado y su blind index
- **WHEN** se busca por el blind index del email ingresado en login
- **THEN** se localiza al usuario sin descifrar la columna de email
