# guardias-crud Specification

## Purpose
TBD - created by archiving change encuentros-y-guardias. Update Purpose after archive.
## Requirements
### Requirement: Registrar guardia (TUTOR)

El sistema SHALL permitir a un usuario con rol TUTOR registrar una guardia con `materia_id`, `cohorte_id`, `fecha`, `hora_inicio`, `hora_fin`. Los campos `titulo` y `observaciones` son opcionales. El `tutor_id` se toma automáticamente de la sesión (JWT), no del body.

#### Scenario: Tutor registra guardia

- **WHEN** un TUTOR autenticado crea una guardia con `materia_id`, `cohorte_id`, `fecha`, `hora_inicio`, `hora_fin`
- **THEN** el sistema almacena `tutor_id` = `current_user.user_id`
- **AND** retorna 201 con los datos de la guardia

#### Scenario: Tutor no puede setear tutor_id de otro

- **WHEN** un TUTOR intenta crear una guardia con `tutor_id` de otro usuario en el body
- **THEN** el sistema ignora el `tutor_id` del body (o retorna 422 si el schema lo rechaza con `extra='forbid'`)
- **AND** usa `current_user.user_id` como `tutor_id`

#### Scenario: Datos requeridos faltantes

- **WHEN** se intenta crear una guardia sin `materia_id`
- **THEN** el sistema retorna 422 con detalle de validación

### Requirement: Listar guardias propias (TUTOR)

El sistema SHALL permitir al TUTOR listar solo sus propias guardias. Un TUTOR no puede ver guardias de otros tutores.

#### Scenario: Tutor lista sus guardias

- **WHEN** un TUTOR solicita `GET /api/guardias`
- **THEN** el sistema retorna solo las guardias donde `tutor_id == current_user.user_id`

### Requirement: Listar todas las guardias (COORDINADOR, ADMIN)

El sistema SHALL permitir a COORDINADOR y ADMIN listar todas las guardias del tenant, con filtros opcionales: `materia_id`, `cohorte_id`, `tutor_id`, `fecha_desde`, `fecha_hasta`.

#### Scenario: Coordinador lista todas las guardias

- **WHEN** un COORDINADOR solicita `GET /api/guardias`
- **THEN** el sistema retorna todas las guardias del tenant (no filtradas por tutor)

#### Scenario: Coordinador filtra por materia

- **WHEN** un COORDINADOR solicita `GET /api/guardias?materia_id=<uuid>`
- **THEN** el sistema retorna solo las guardias de esa materia

### Requirement: Editar guardia (TUTOR — solo propias)

El sistema SHALL permitir al TUTOR editar `fecha`, `hora_inicio`, `hora_fin`, `titulo` y `observaciones` de sus propias guardias.

#### Scenario: Tutor edita su guardia

- **WHEN** un TUTOR modifica `observaciones` de una guardia propia vía `PATCH /api/guardias/<guardia_id>`
- **THEN** el sistema actualiza el campo y retorna la guardia

#### Scenario: Tutor intenta editar guardia ajena

- **WHEN** un TUTOR intenta editar una guardia cuyo `tutor_id` no coincide con `current_user.user_id`
- **THEN** el sistema retorna 404 (no 403, para no revelar existencia)

### Requirement: Soft-delete de guardia (TUTOR — solo propias)

El sistema SHALL permitir al TUTOR soft-deletear sus propias guardias.

#### Scenario: Tutor soft-deletea su guardia

- **WHEN** un TUTOR solicita `DELETE /api/guardias/<guardia_id>` sobre una guardia propia
- **THEN** la guardia se marca con `deleted_at = now()`
- **AND** el sistema retorna 204

### Requirement: Exportar guardias a CSV (COORDINADOR, ADMIN)

El sistema SHALL permitir exportar todas las guardias del tenant a un archivo CSV con columnas: `tutor_nombre`, `materia_codigo`, `cohorte_nombre`, `fecha`, `hora_inicio`, `hora_fin`, `titulo`, `observaciones`.

#### Scenario: Export CSV con datos

- **WHEN** un COORDINADOR solicita `GET /api/guardias/export`
- **THEN** el sistema retorna `Content-Type: text/csv` con header `Content-Disposition: attachment; filename=guardias.csv`
- **AND** el CSV contiene los nombres descriptivos (no UUIDs) de tutor, materia y cohorte
- **AND** las guardias soft-deleteadas no se incluyen

#### Scenario: Export CSV sin datos

- **WHEN** no hay guardias en el tenant
- **THEN** el sistema retorna CSV solo con la fila de headers

