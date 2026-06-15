# padron-email-cifrado Specification

## Purpose
TBD - created by archiving change c-09-padron-ingesta-moodle. Update Purpose after archive.
## Requirements
### Requirement: Email del alumno cifrado en reposo

El sistema SHALL almacenar el email de cada `EntradaPadron` cifrado en reposo con AES-256, espejando el patrón de `Usuario`: un `email_hash` determinístico para búsqueda/matching y un `email_enc` con el ciphertext. El email en texto plano MUST NOT persistirse en ninguna columna.

#### Scenario: Importar cifra el email y no guarda texto plano

- **WHEN** se importa un padrón con entradas que incluyen email
- **THEN** cada `EntradaPadron` persiste `email_hash` y `email_enc`
- **AND** ninguna columna de la fila contiene el email en texto plano

#### Scenario: Leer una entrada descifra el email

- **WHEN** se listan las entradas de una versión vía la API
- **THEN** el sistema descifra `email_enc` y devuelve el email en claro en la respuesta

#### Scenario: Matching email→usuario usa hash determinístico

- **WHEN** se compara el email de una fila contra los usuarios del tenant
- **THEN** el matching usa el hash determinístico del email normalizado (`strip().lower()`), sin exponer ni comparar texto plano persistido

### Requirement: Migración de filas existentes a email cifrado

El sistema SHALL migrar las filas de `entrada_padron` existentes desde el email en texto plano hacia `email_hash` + `email_enc`, sin pérdida de filas.

#### Scenario: Filas previas quedan cifradas tras la migración

- **WHEN** se aplica la migración `021`
- **THEN** cada fila existente tiene su `email_hash` y `email_enc` poblados a partir del email previo
- **AND** la columna de email en texto plano deja de existir

