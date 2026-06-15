# padron-vaciar-autorizacion Specification

## Purpose
TBD - created by archiving change c-09-padron-ingesta-moodle. Update Purpose after archive.
## Requirements
### Requirement: Vaciado de padrón exige permiso propio

El sistema SHALL exigir el permiso RBAC `padron:vaciar` para la operación de vaciado de padrón, declarado explícitamente en el catálogo de permisos y aplicado fail-closed (sin el permiso → 403). El vaciado MUST NOT reusar `padron:importar`.

#### Scenario: Sin el permiso padron:vaciar se rechaza

- **WHEN** un usuario sin el permiso `padron:vaciar` invoca el endpoint de vaciado
- **THEN** el sistema responde 403

#### Scenario: La identidad se toma de la sesión JWT

- **WHEN** se evalúa la autorización de vaciado
- **THEN** el sistema usa la identidad, los roles y el tenant del JWT verificado, nunca un parámetro de la petición

### Requirement: Reglas de pertenencia en el vaciado (RN-04/RN-05)

El sistema SHALL aplicar reglas de pertenencia al vaciar versiones de padrón: un PROFESOR SHALL poder vaciar únicamente versiones cuyo `cargado_por` sea su propio `id`; un COORDINADOR (y ADMIN) SHALL poder vaciar cualquier versión del tenant.

#### Scenario: PROFESOR vacía su propia versión

- **WHEN** un PROFESOR vacía una versión donde `version.cargado_por == current_user.id`
- **THEN** la operación se ejecuta y las versiones/entradas se marcan como soft-deleted

#### Scenario: PROFESOR no puede vaciar versión ajena

- **WHEN** un PROFESOR intenta vaciar una versión donde `version.cargado_por != current_user.id`
- **THEN** el sistema rechaza la operación (403) y no modifica ninguna fila

#### Scenario: COORDINADOR vacía cualquier versión

- **WHEN** un COORDINADOR vacía una versión cargada por otro usuario del mismo tenant
- **THEN** la operación se ejecuta correctamente

### Requirement: Vaciado por soft delete

El sistema SHALL implementar el vaciado mediante soft delete (marcado de `deleted_at`), nunca borrado físico, preservando el rastro de auditoría append-only.

#### Scenario: Vaciar marca deleted_at sin borrar físicamente

- **WHEN** se vacía un padrón
- **THEN** las versiones y entradas afectadas quedan con `deleted_at` poblado
- **AND** ninguna fila se elimina físicamente de la base

