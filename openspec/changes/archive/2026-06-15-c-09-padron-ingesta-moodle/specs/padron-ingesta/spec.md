## ADDED Requirements

### Requirement: Preview de padrón sin persistir

El sistema SHALL permitir previsualizar un archivo de padrón (xlsx/csv) devolviendo las filas parseadas y el matching de email→usuario, sin escribir ninguna fila en la base de datos.

#### Scenario: Preview devuelve filas sin persistir

- **WHEN** un usuario con permiso `padron:importar` sube un archivo xlsx válido al endpoint de preview
- **THEN** el sistema responde con las filas parseadas (nombre, apellidos, email, comisión, regional) y su `matched_usuario_id` cuando el email coincide con un usuario del tenant
- **AND** no se crea ninguna `VersionPadron` ni `EntradaPadron` en la base

#### Scenario: Archivo con extensión peligrosa es rechazado

- **WHEN** un usuario sube un archivo con extensión peligrosa (p. ej. `.exe`)
- **THEN** el sistema responde 400 sin parsear ni persistir

### Requirement: Confirmación atómica de importación con versionado

El sistema SHALL crear una nueva `VersionPadron` activa junto con sus `EntradaPadron` en una sola transacción atómica, y SHALL desactivar cualquier versión previa de la misma `(materia_id, cohorte_id)`.

#### Scenario: Importar crea versión activa y desactiva la previa

- **WHEN** existe una versión activa para `(materia, cohorte)` y se importa una nueva
- **THEN** la nueva versión queda `activa = true`
- **AND** la versión previa queda `activa = false`

#### Scenario: Activar una versión desactiva las demás de la misma materia-cohorte

- **WHEN** se activa explícitamente una versión existente vía el endpoint de activación
- **THEN** esa versión queda `activa = true`
- **AND** todas las demás versiones de la misma `(materia, cohorte)` quedan `activa = false`

### Requirement: Fallback de encoding en import csv

El sistema SHALL decodificar archivos csv intentando primero UTF-8 y, si falla, SHALL reintentar con Latin-1, para tolerar exportaciones de Moodle con codificaciones heredadas.

#### Scenario: CSV en Latin-1 se parsea correctamente

- **WHEN** se importa un csv codificado en Latin-1 con caracteres acentuados que no son válidos en UTF-8
- **THEN** el sistema decodifica con Latin-1 y devuelve las filas con los acentos correctos

### Requirement: Entrada de padrón sin cuenta de usuario

El sistema SHALL aceptar entradas de padrón cuyo email no corresponde a ningún usuario del sistema, persistiéndolas con `usuario_id = NULL`.

#### Scenario: Alumno sin cuenta se persiste con usuario_id nulo

- **WHEN** una fila del padrón tiene un email que no coincide con ningún usuario del tenant
- **THEN** la `EntradaPadron` se crea con `usuario_id = NULL` y el resto de sus datos intactos
