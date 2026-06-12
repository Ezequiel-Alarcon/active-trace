# calificacion-import Specification

## Purpose

Allow authorized users to import grades from LMS (Moodle) into the system via a two-step flow: preview without persisting, then confirm to persist. Also supports importing completion reports (TPs without a grade, stored as `nota = null`). Every import is audited with the operator, timestamp, and import batch ID.

## ADDED Requirements

### Requirement: Import preview parses file and returns parsed rows without persisting

The system SHALL accept a CSV or Excel file via `POST /api/calificaciones/import/preview`, parse each row, validate format and references (materia, usuario, asignacion exist and belong to tenant), and return a structured preview with a `preview_token` (UUID) and a list of parsed rows including any validation warnings — without inserting any record into the database.

#### Scenario: Preview with valid file returns parsed rows and token

- **WHEN** user with `calificaciones:importar` calls `POST /api/calificaciones/import/preview` with a CSV containing 10 valid grade rows for materia `M1`, usuarios `U1`–`U10`, asignacion `A1`, and numeric grades
- **THEN** response is `200 OK` with `preview_token` (UUID) and `rows` array of 10 objects with `usuario_id`, `materia_id`, `asignacion_id`, `nota`, `warnings: []`
- **AND** no `Calificacion` records exist in the database for this import

#### Scenario: Preview detects unknown usuario and returns warning

- **WHEN** user calls `POST /api/calificaciones/import/preview` with a CSV row containing `usuario_email: "unknown@example.com"` that does not match any `Usuario` in the tenant
- **THEN** that row is returned with `warnings: ["Usuario no encontrado: unknown@example.com"]`
- **AND** `valid: false` for that row
- **AND** no record is persisted

#### Scenario: Preview detects duplicate row within same file

- **WHEN** user calls `POST /api/calificaciones/import/preview` and the CSV contains two rows with the same `usuario_id` and `asignacion_id`
- **THEN** the second row is returned with `warnings: ["Duplicado en archivo para este usuario y asignación"]`
- **AND** `valid: false` for that row

#### Scenario: Preview token expires after 15 minutes

- **WHEN** user obtains a `preview_token` from `POST /api/calificaciones/import/preview`
- **AND** 16 minutes pass
- **AND** user calls `POST /api/calificaciones/import/confirm` with that token
- **THEN** response is `410 Gone` with `{"detail": "Preview expirado"}`

#### Scenario: Preview requires calificaciones:importar permission

- **WHEN** user WITHOUT `calificaciones:importar` calls `POST /api/calificaciones/import/preview`
- **THEN** response is `403 Forbidden`

### Requirement: Import confirm persists all valid rows and rejects invalid ones

The system SHALL accept a `preview_token` via `POST /api/calificaciones/import/confirm`, retrieve the parsed rows from the preview session, persist all rows marked `valid: true` as `Calificacion` records with `origen = Importado` and a shared `import_batch_id`, skip rows marked `valid: false`, and return a summary of persisted, skipped, and failed counts.

#### Scenario: Confirm persists valid rows and assigns import_batch_id

- **WHEN** user calls `POST /api/calificaciones/import/confirm` with a valid `preview_token` that has 8 `valid: true` rows and 2 `valid: false` rows
- **THEN** exactly 8 new `Calificacion` records are created with `origen = Importado`
- **AND** all 8 share the same `import_batch_id` (UUID)
- **AND** response is `200 OK` with `{persisted: 8, skipped: 2, failed: 0}`
- **AND** the `preview_token` is invalidated (cannot be used again)

#### Scenario: Confirm fails if any database constraint is violated

- **WHEN** user calls `POST /api/calificaciones/import/confirm` with a valid `preview_token`
- **AND** a uniqueness constraint prevents one of the valid rows (e.g., a `Calificacion` already exists for that materia_id, usuario_id, asignacion_id combination)
- **THEN** that row fails and is counted in `failed`
- **AND** other valid rows are persisted
- **AND** response is `200 OK` with `{persisted: N, skipped: 2, failed: 1}`

#### Scenario: Confirm requires calificaciones:importar permission

- **WHEN** user WITHOUT `calificaciones:importar` calls `POST /api/calificaciones/import/confirm`
- **THEN** response is `403 Forbidden`

### Requirement: Completion report import sets nota to null

The system SHALL accept a completion report file (CSV/Excel with columns: `usuario_email`, `materia_id`, `asignacion_id`) via `POST /api/calificaciones/import/preview` with query parameter `type=completion`. On confirm, those rows are persisted with `nota = null` and `origen = Importado`.

#### Scenario: Completion report import creates records with null nota

- **WHEN** user calls `POST /api/calificaciones/import/preview?type=completion` with a CSV containing 5 rows (usuario_email, materia_id, asignacion_id) with no grade columns
- **THEN** preview returns 5 rows with `nota: null` and `warnings: []`
- **AND** confirm persists 5 `Calificacion` records with `nota = null`

#### Scenario: Completion report rows are marked valid only if usuario and asignacion exist

- **WHEN** user submits a completion report with a row where `usuario_email` does not match any `Usuario`
- **THEN** that row is returned with `valid: false` and `warnings: ["Usuario no encontrado"]`

### Requirement: Audit log records import batch

The system SHALL write an `AUDITORIA` entry for each confirmed import with `operacion = CALIFICACIONES_IMPORTAR`, `usuario_id` from JWT, `tenant_id` from JWT, `detalle` containing `import_batch_id`, `total_filas`, `persistidas`, `omitidas`, and `fecha`.

#### Scenario: Audit entry created on confirm

- **WHEN** user confirms an import with `preview_token` that has 10 valid rows
- **THEN** an `AUDITORIA` record is created with `operacion: CALIFICACIONES_IMPORTAR`
- **AND** `detalle` includes `{"import_batch_id": "<uuid>", "total_filas": 10, "persistidas": 10, "omitidas": 0}`