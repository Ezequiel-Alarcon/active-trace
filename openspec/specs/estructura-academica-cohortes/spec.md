# estructura-academica-cohortes Specification

## Purpose
TBD - created by archiving change estructura-academica. Update Purpose after archive.
## Requirements
### Requirement: System SHALL create a new cohorte with unique nombre within carrera and tenant

The system SHALL create a new cohorte when ADMIN provides valid `carrera_id`, `nombre`, `anio`, `vig_desde`, and optional `vig_hasta`. The combination `(tenant_id, carrera_id, nombre)` SHALL be unique. The carrera SHALL exist and be in `Activa` state. `vig_hasta = NULL` means the cohorte is open-ended.

#### Scenario: Create cohorte succeeds

- **WHEN** admin calls `POST /api/admin/cohortes` with `{"carrera_id": "<uuid>", "nombre": "2025-A", "anio": 2025, "vig_desde": "2025-03-01"}`
- **AND** the carrera exists and is `Activa`
- **THEN** response is `201 Created` with the created cohorte object
- **AND** `tenant_id` matches the current tenant from session
- **AND** `estado` defaults to `Activa`
- **AND** `vig_hasta` is `null`

#### Scenario: Create cohorte with carrera inactiva fails

- **WHEN** admin calls `POST /api/admin/cohortes` with a `carrera_id` whose carrera has `estado: Inactiva`
- **THEN** response is `422 Unprocessable Entity` with `{"detail": "No se puede crear una cohorte para una carrera inactiva"}`

#### Scenario: Create cohorte with non-existent carrera fails

- **WHEN** admin calls `POST /api/admin/cohortes` with a non-existent `carrera_id`
- **THEN** response is `422 Unprocessable Entity` with `{"detail": "La carrera especificada no existe"}`

#### Scenario: Create duplicate cohorte nombre within same carrera fails

- **WHEN** admin calls `POST /api/admin/cohortes` with `{"carrera_id": "X", "nombre": "2025-A"}` and a cohorte with nombre `2025-A` already exists for carrera X in this tenant
- **THEN** response is `409 Conflict` with `{"detail": "Ya existe una cohorte con ese nombre para esta carrera en este tenant"}`

#### Scenario: Create cohorte with vig_hasta before vig_desde fails

- **WHEN** admin calls `POST /api/admin/cohortes` with `{"carrera_id": "<uuid>", "nombre": "2025-B", "anio": 2025, "vig_desde": "2025-12-01", "vig_hasta": "2025-01-01"}`
- **THEN** response is `422 Unprocessable Entity` with `{"detail": "vig_hasta debe ser posterior a vig_desde"}`

### Requirement: System SHALL list all non-soft-deleted cohortes for the current tenant

The system SHALL return all non-soft-deleted cohortes for the current tenant, optionally filtered by `carrera_id` and/or `estado`.

#### Scenario: List cohortes returns tenant-scoped results

- **WHEN** admin calls `GET /api/admin/cohortes`
- **THEN** response is `200 OK` with JSON array of cohorte objects
- **AND** each has `id`, `tenant_id`, `carrera_id`, `nombre`, `anio`, `vig_desde`, `vig_hasta`, `estado`, `created_at`, `updated_at`
- **AND** no soft-deleted cohortes are included

#### Scenario: List cohortes filtered by carrera

- **WHEN** admin calls `GET /api/admin/cohortes?carrera_id=<uuid>`
- **THEN** response is `200 OK` with JSON array containing only cohortes for that carrera

### Requirement: System SHALL return a single cohorte by id

The system SHALL return a single cohorte by id, scoped to the current tenant.

#### Scenario: Get existing cohorte

- **WHEN** admin calls `GET /api/admin/cohortes/{cohorte_id}` for a valid cohorte
- **THEN** response is `200 OK` with the cohorte object

#### Scenario: Get non-existent cohorte returns 404

- **WHEN** admin calls `GET /api/admin/cohortes/{unknown_id}`
- **THEN** response is `404 Not Found` with `{"detail": "Cohorte no encontrada"}`

### Requirement: System SHALL update cohorte fields when admin provides valid data

The system SHALL update cohorte fields. Changing `carrera_id` is NOT allowed. Activating an inactive cohorte whose carrera is inactive SHALL be rejected.

#### Scenario: Update cohorte nombre

- **WHEN** admin calls `PATCH /api/admin/cohortes/{cohorte_id}` with `{"nombre": "2025-B"}`
- **THEN** response is `200 OK` with updated cohorte
- **AND** `updated_at` is refreshed

#### Scenario: Update cohorte estado to Activa when carrera is inactive fails

- **WHEN** an inactive cohorte belongs to an inactive carrera
- **AND** admin calls `PATCH /api/admin/cohortes/{cohorte_id}` with `{"estado": "Activa"}`
- **THEN** response is `422 Unprocessable Entity` with `{"detail": "No se puede activar una cohorte si la carrera esta inactiva"}`

### Requirement: System SHALL soft-delete a cohorte without physical deletion

The system SHALL soft-delete a cohorte.

#### Scenario: Delete cohorte soft-deletes

- **WHEN** admin calls `DELETE /api/admin/cohortes/{cohorte_id}`
- **THEN** response is `204 No Content`
- **AND** `deleted_at` is set on the cohorte
- **AND** subsequent list queries do not return this cohorte

### Requirement: System SHALL validate carrera_id belongs to current tenant on write operations

The system SHALL ensure that `carrera_id` references a carrera that belongs to the current tenant. Cross-tenant references SHALL be rejected.

#### Scenario: Create cohorte with carrera from another tenant fails

- **WHEN** admin of tenant A calls `POST /api/admin/cohortes` with a `carrera_id` that belongs to tenant B
- **THEN** response is `422 Unprocessable Entity` (carrera not found in this tenant)

