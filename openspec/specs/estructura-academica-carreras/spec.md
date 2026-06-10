# estructura-academica-carreras Specification

## Purpose
TBD - created by archiving change estructura-academica. Update Purpose after archive.
## Requirements
### Requirement: System SHALL create a new carrera with unique codigo per tenant

The system SHALL create a new carrera when ADMIN provides valid `codigo` and `nombre`. The `codigo` SHALL be unique within the tenant. The `estado` defaults to `Activa`.

#### Scenario: Create carrera succeeds

- **WHEN** admin calls `POST /api/admin/carreras` with `{"codigo": "ING-INF", "nombre": "Ingenieria en Informatica"}`
- **THEN** response is `201 Created` with the created carrera object
- **AND** `id` is a UUID
- **AND** `tenant_id` matches the current tenant from session
- **AND** `estado` is `Activa`
- **AND** `created_at` and `updated_at` are set

#### Scenario: Create carrera with duplicate codigo fails

- **WHEN** admin calls `POST /api/admin/carreras` with `{"codigo": "ING-INF"}` and a carrera with codigo `ING-INF` already exists in the tenant
- **THEN** response is `409 Conflict` with `{"detail": "Ya existe una carrera con ese codigo en este tenant"}`

#### Scenario: Create carrera with extra fields fails

- **WHEN** admin calls `POST /api/admin/carreras` with `{"codigo": "XXX", "nombre": "Test", "extra": "no-permitido"}`
- **THEN** response is `422 Unprocessable Entity` (extra fields forbidden by `extra='forbid'`)

### Requirement: System SHALL list all non-soft-deleted carreras for the current tenant

The system SHALL return all non-soft-deleted carreras for the current tenant, optionally filtered by `estado`.

#### Scenario: List carreras returns tenant-scoped results

- **WHEN** admin calls `GET /api/admin/carreras`
- **THEN** response is `200 OK` with JSON array of carrera objects
- **AND** each has `id`, `tenant_id`, `codigo`, `nombre`, `estado`, `created_at`, `updated_at`
- **AND** no soft-deleted carreras are included
- **AND** only carreras from the current tenant are returned

#### Scenario: List carreras filtered by estado

- **WHEN** admin calls `GET /api/admin/carreras?estado=Activa`
- **THEN** response is `200 OK` with JSON array containing only carreras where `estado == Activa`

### Requirement: System SHALL return a single carrera by id

The system SHALL return a single carrera by id, scoped to the current tenant.

#### Scenario: Get existing carrera

- **WHEN** admin calls `GET /api/admin/carreras/{carrera_id}` for a valid carrera
- **THEN** response is `200 OK` with the carrera object

#### Scenario: Get non-existent carrera returns 404

- **WHEN** admin calls `GET /api/admin/carreras/{unknown_id}`
- **THEN** response is `404 Not Found` with `{"detail": "Carrera no encontrada"}`

#### Scenario: Get carrera from another tenant returns 404

- **WHEN** admin of tenant A calls `GET /api/admin/carreras/{carrera_id_from_tenant_B}`
- **THEN** response is `404 Not Found`

### Requirement: System SHALL update carrera fields when admin provides valid data

The system SHALL update carrera fields (codigo, nombre, estado) when admin provides valid data. Changing `codigo` to an existing one SHALL be rejected.

#### Scenario: Update carrera nombre

- **WHEN** admin calls `PATCH /api/admin/carreras/{carrera_id}` with `{"nombre": "Ingenieria Informatica"}`
- **THEN** response is `200 OK` with updated carrera
- **AND** `updated_at` is refreshed

#### Scenario: Update carrera to duplicate codigo fails

- **WHEN** admin calls `PATCH /api/admin/carreras/{carrera_id}` with `{"codigo": "ING-IND"}` and another carrera already has codigo `ING-IND`
- **THEN** response is `409 Conflict`

#### Scenario: Update carrera estado to Inactiva

- **WHEN** admin calls `PATCH /api/admin/carreras/{carrera_id}` with `{"estado": "Inactiva"}`
- **THEN** response is `200 OK` with `estado: "Inactiva"`

### Requirement: System SHALL soft-delete a carrera without physical deletion

The system SHALL soft-delete a carrera (set `deleted_at`) without physical deletion.

#### Scenario: Delete carrera soft-deletes

- **WHEN** admin calls `DELETE /api/admin/carreras/{carrera_id}`
- **THEN** response is `204 No Content`
- **AND** `deleted_at` is set on the carrera
- **AND** subsequent list queries do not return this carrera

### Requirement: System SHALL deny access to estructura endpoints for users without estructura:gestionar

The system SHALL deny access to estructura endpoints for users without `estructura:gestionar` permission.

#### Scenario: Non-admin user cannot list carreras

- **WHEN** user WITHOUT `estructura:gestionar` calls `GET /api/admin/carreras`
- **THEN** response is `403 Forbidden` with `{"detail": "No tiene el permiso: estructura:gestionar"}`

#### Scenario: Non-admin user cannot create carrera

- **WHEN** user WITHOUT `estructura:gestionar` calls `POST /api/admin/carreras`
- **THEN** response is `403 Forbidden`

