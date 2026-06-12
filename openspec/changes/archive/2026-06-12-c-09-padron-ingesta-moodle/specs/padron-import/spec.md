## ADDED Requirements

### Requirement: Padron preview returns parsed rows without persisting

The system SHALL parse an uploaded `.xlsx` or `.csv` file and return a preview of the detected rows without creating any database records. The preview SHALL be available for the user to review before confirming the import.

#### Scenario: Preview returns parsed rows from xlsx

- **WHEN** user uploads an `.xlsx` file to `POST /api/padrones/preview`
- **THEN** the response contains a list of parsed rows with `nombre`, `apellidos`, `email`, `comision`, `regional`
- **AND** no `VersionPadron` or `EntradaPadron` records exist in the database

#### Scenario: Preview returns parsed rows from csv

- **WHEN** user uploads a `.csv` file to `POST /api/padrones/preview`
- **THEN** the response contains the same structure as xlsx preview
- **AND** encoding is handled (UTF-8 or Latin-1)

#### Scenario: Preview fails on malformed file

- **WHEN** user uploads a file that is not a valid xlsx or csv
- **THEN** the response is `400 Bad Request` with a descriptive error message

### Requirement: Padron import requires confirmation step

The system SHALL require an explicit confirmation after the preview step. The user MUST call `POST /api/padrones` with the same data or a reference to the preview session to create the padron version.

#### Scenario: Import succeeds after valid preview

- **WHEN** user calls `POST /api/padrones` with the preview data
- **THEN** a `VersionPadron` and its `EntradaPadron` records are created
- **AND** the response is `201 Created` with the new version details

#### Scenario: Import fails if no preview was requested

- **WHEN** user calls `POST /api/padrones` without a prior preview
- **THEN** the response is `400 Bad Request` asking for a preview first

### Requirement: Padron import rejects files over 50MB

The system SHALL reject padron files larger than 50MB with `413 Request Entity Too Large`.

#### Scenario: File too large returns 413

- **WHEN** user uploads a file larger than 50MB to `POST /api/padrones/preview`
- **THEN** the response is `413 Request Entity Too Large`
- **AND** no processing occurs

### Requirement: Padron import rejects dangerous file extensions

The system SHALL reject files with extensions that could be executed on the server (e.g., `.exe`, `.php`, `.sh`) with `400 Bad Request`.

#### Scenario: Executable file rejected

- **WHEN** user uploads a file named `data.exe`
- **THEN** the response is `400 Bad Request`
- **AND** the error message explains the file type is not allowed

### Requirement: Vaciar datos de materia removes all padron and calificacion data

The system SHALL delete all `VersionPadron`, `EntradaPadron`, and `Calificacion` records for a given `(materia_id, cohorte_id)` when the user requests to vacate the materia data (F1.5, RN-04).

#### Scenario: Vaciar datos removes padron and calificaciones for the materia-cohorte

- **WHEN** user calls `DELETE /api/padrones/materia/{materia_id}/cohorte/{cohorte_id}`
- **THEN** all `VersionPadron` with matching `materia_id` and `cohorte_id` are soft-deleted
- **AND** all `EntradaPadron` linked to those versions are soft-deleted
- **AND** all `Calificacion` for the same `materia_id` and `cohorte_id` are soft-deleted
- **AND** audit log records `PADRON_CARGAR` with `filas_afectadas = 0` and action detail indicating vaciado

#### Scenario: Vaciar datos requires padron:importar permission

- **WHEN** user without `padron:importar` permission calls `DELETE /api/padrones/materia/{materia_id}/cohorte/{cohorte_id}`
- **THEN** the response is `403 Forbidden`