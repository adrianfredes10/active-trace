# field-encryption Specification

## Purpose

Cifrar en reposo los atributos sensibles (`[cifrado]`: DNI, CUIL, CBU, email PII) con AES-256, ofreciendo un tipo de columna SQLAlchemy para cifrado transparente y sin exponer valores en claro en logs.
## Requirements
### Requirement: Cifrado AES-256 en reposo para atributos sensibles

El sistema SHALL proveer una utilidad de cifrado simétrico AES-256 para los atributos marcados como sensibles (`[cifrado]`: DNI, CUIL, CBU, alias CBU, email PII). La utilidad SHALL exponer operaciones de cifrado y descifrado que usen la clave de cifrado de la configuración (`ENCRYPTION_KEY`, 32 bytes). El cifrado SHALL ser autenticado (detecta manipulación del texto cifrado). Los valores en claro NUNCA SHALL escribirse en logs ni exponerse en representaciones de texto de los modelos.

#### Scenario: Round-trip de cifrado

- **WHEN** se cifra un valor en claro y luego se descifra el resultado
- **THEN** el valor recuperado es idéntico al original

#### Scenario: El texto cifrado no es el texto plano

- **WHEN** se cifra un valor en claro
- **THEN** el texto cifrado resultante es distinto del valor en claro y no lo contiene de forma legible

#### Scenario: Detección de manipulación

- **WHEN** se intenta descifrar un texto cifrado alterado
- **THEN** la operación falla en lugar de devolver un valor incorrecto

### Requirement: Tipo de columna cifrada para persistencia transparente

El sistema SHALL proveer un tipo de columna de SQLAlchemy que cifre el valor al escribir en la base de datos y lo descifre al leer, de modo que el código de aplicación opere con texto plano en memoria mientras la base almacena únicamente texto cifrado.

#### Scenario: Persistencia cifrada transparente

- **GIVEN** una columna que usa el tipo de columna cifrada
- **WHEN** se persiste una entidad con un valor en claro en esa columna
- **THEN** la base de datos almacena el valor cifrado
- **AND** al releer la entidad, la aplicación obtiene el valor en claro original

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

