## ADDED Requirements

### Requirement: VersionPadron is activated atomically and deactivates previous version

The system SHALL ensure that only one `VersionPadron` with `activa = true` exists per `(materia_id, cohorte_id)` pair at any given time. Activating a new version MUST deactivate all previous versions for the same `(materia_id, cohorte_id)` within a single database transaction.

#### Scenario: Activating a new version deactivates the previous one

- **WHEN** user activates version V2 for `(materia_id=M1, cohorte_id=C1)`
- **THEN** version V1 for the same `(materia_id, cohorte_id)` has `activa = false`
- **AND** V2 has `activa = true`
- **AND** the operation is atomic (both changes or neither)

#### Scenario: No active version exists initially

- **WHEN** user activates the first version for a `(materia_id, cohorte_id)` pair
- **THEN** the version is activated successfully
- **AND** no other version is affected

#### Scenario: Concurrent activation requests for same materia-cohorte

- **WHEN** two concurrent requests try to activate different versions for the same `(materia_id, cohorte_id)`
- **THEN** only one succeeds
- **AND** the other receives an error response

### Requirement: EntradaPadron can exist without a linked Usuario

The system SHALL allow an `EntradaPadron` record to be persisted with `usuario_id = NULL` when the student does not yet have a user account in the system.

#### Scenario: EntradaPadron persisted without usuario_id

- **WHEN** a padron entry is imported with an email that does not match any `Usuario.email` in the same tenant
- **THEN** the entry is persisted with `usuario_id = NULL`
- **AND** the `nombre`, `apellidos`, `email`, `comision`, `regional` fields are stored

#### Scenario: EntradaPadron linked when usuario registers later

- **WHEN** a student registers and their email matches an existing `EntradaPadron.email` for the same tenant
- **THEN** the system MAY link the `EntradaPadron` to the new `Usuario` record
- **AND** the `usuario_id` field is populated

### Requirement: Padron import creates a new VersionPadron with all EntradaPadron entries

The system SHALL create a new `VersionPadron` record and associate it with all `EntradaPadron` entries parsed from the uploaded file, as part of a single atomic operation.

#### Scenario: Import creates version and entries atomically

- **WHEN** user confirms the padron import with 100 rows in the preview
- **THEN** exactly one `VersionPadron` record is created
- **AND** exactly 100 `EntradaPadron` records are created, all linked to that version
- **AND** if any row fails validation, NO records are created (full rollback)

### Requirement: Padron import is scoped to the current tenant

The system SHALL associate all imported padron records with the `tenant_id` extracted from the authenticated session. The import MUST reject any attempt to specify a different `tenant_id`.

#### Scenario: Import respects tenant isolation

- **WHEN** tenant A imports a padron for materia M1
- **THEN** all `VersionPadron` and `EntradaPadron` records have `tenant_id = tenant_A`
- **AND** tenant B cannot see, query, or modify these records

### Requirement: Padron import generates an audit log entry

The system SHALL emit an `AuditLog` entry with action code `PADRON_CARGAR` and `filas_afectadas` equal to the number of `EntradaPadron` records created.

#### Scenario: Audit log records padron import

- **WHEN** user imports a padron with 50 rows
- **THEN** an `AuditLog` entry is created with `accion = "PADRON_CARGAR"`
- **AND** `filas_afectadas = 50`
- **AND** `actor_id` is the authenticated user who performed the import