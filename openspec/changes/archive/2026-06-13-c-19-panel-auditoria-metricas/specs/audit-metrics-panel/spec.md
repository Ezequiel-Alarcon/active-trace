## ADDED Requirements

### Requirement: Actions per day time series
The system SHALL return a time series of action counts grouped by day, optionally filtered by user.

#### Scenario: Returns actions grouped by day
- **WHEN** a user with `auditoria:ver` calls `GET /api/audit/metrics/actions-per-day`
- **THEN** the system returns a list of `{date, count}` objects ordered by date ascending

#### Scenario: Filters by actor_id when provided
- **WHEN** a user calls `GET /api/audit/metrics/actions-per-day?actor_id=<uuid>`
- **THEN** only actions by that actor are counted in the response

#### Scenario: Applies tenant scope automatically
- **WHEN** a user calls the endpoint
- **THEN** only entries from the user's tenant are included in the aggregation

#### Scenario: Applies COORDINADOR scope
- **WHEN** a COORDINADOR (without `ver_todos`) calls the endpoint
- **THEN** only entries where `materia_id` matches the user's assigned materias are included

### Requirement: Communication status by docente/materia
The system SHALL return counts of communication actions (`COMUNICACION_ENVIAR`, `COMUNICACION_APROBAR`) grouped by status, docente, and materia.

#### Scenario: Returns grouped communication counts
- **WHEN** a user with `auditoria:ver` calls `GET /api/audit/metrics/comunicacion-status`
- **THEN** the system returns a list of `{materia_id, docente_id, pending, sending, ok, failed, cancelled}` counts

#### Scenario: Respects tenant scope
- **WHEN** a user calls the endpoint
- **THEN** only entries from the user's tenant are included

#### Scenario: Respects COORDINADOR scope
- **WHEN** a COORDINADOR (without `ver_todos`) calls the endpoint
- **THEN** only entries for materias the user coordinates are returned

### Requirement: Interactions by docente/materia
The system SHALL return interaction counts grouped by docente, materia, and action type.

#### Scenario: Returns interaction summaries
- **WHEN** a user with `auditoria:ver` calls `GET /api/audit/metrics/interactions`
- **THEN** the system returns a list of `{materia_id, docente_id, accion, count}` entries

#### Scenario: Respects tenant scope
- **WHEN** a user calls the endpoint
- **THEN** only entries from the user's tenant are included

#### Scenario: Respects COORDINADOR scope
- **WHEN** a COORDINADOR (without `ver_todos`) calls the endpoint
- **THEN** only entries for materias the user coordinates are returned

### Requirement: Last actions log
The system SHALL return the most recent audit log entries with a configurable limit (default 200, max 500).

#### Scenario: Returns last actions ordered by date descending
- **WHEN** a user with `auditoria:ver` calls `GET /api/audit/metrics/last-actions`
- **THEN** the system returns up to 200 most recent entries ordered by `fecha_hora` descending

#### Scenario: Respects limit parameter
- **WHEN** a user calls `GET /api/audit/metrics/last-actions?limit=50`
- **THEN** the system returns at most 50 entries

#### Scenario: Caps limit at 500
- **WHEN** a user calls `GET /api/audit/metrics/last-actions?limit=1000`
- **THEN** the system returns at most 500 entries (capped)

### Requirement: Scope enforcement for COORDINADOR
The system SHALL enforce materia-level scope for COORDINADOR users who only have `auditoria:ver` without `auditoria:ver_todos`.

#### Scenario: ADMIN sees all data
- **WHEN** an ADMIN user calls any metrics endpoint
- **THEN** no materia scope filter is applied

#### Scenario: COORDINADOR sees only their materias
- **WHEN** a COORDINADOR user without `ver_todos` calls any metrics endpoint
- **THEN** the system filters by materia_ids the user is assigned to in `equipo_docente`

#### Scenario: FINANZAS sees all data
- **WHEN** a FINANZAS user calls any metrics endpoint
- **THEN** no materia scope filter is applied
