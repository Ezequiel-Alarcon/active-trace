# programa-materia-crud Specification

## Purpose

Define el ABM de programas de materia. Un programa es un documento asociado a la combinación materia × carrera × cohorte. ADMIN y COORDINADOR pueden crear, editar, consultar y soft-deletear programas. El campo `referencia_archivo` es una string opaca (ruta/URL al archivo almacenado).

## ADDED Requirements

### Requirement: System SHALL create a new programa with unique materia × carrera × cohorte per tenant

The system SHALL create a new programa when the user provides valid `materia_id`, `carrera_id`, `cohorte_id`, `titulo` and optional `referencia_archivo`. The combination `(materia_id, carrera_id, cohorte_id)` SHALL be unique within the tenant.

#### Scenario: Create programa succeeds

- **WHEN** user with `estructura:gestionar` calls `POST /api/programas` with `{"materia_id": "<uuid>", "carrera_id": "<uuid>", "cohorte_id": "<uuid>", "titulo": "Programa Analitico 2025", "referencia_archivo": "/files/prog-001.pdf"}`
- **THEN** response is `201 Created` with the created programa object
- **AND** `id` is a UUID
- **AND** `tenant_id` matches the current tenant from session
- **AND** `referencia_archivo` is the exact string provided
- **AND** `created_at` and `updated_at` are set

#### Scenario: Create programa without referencia_archivo succeeds

- **WHEN** user calls `POST /api/programas` with `{"materia_id": "<uuid>", "carrera_id": "<uuid>", "cohorte_id": "<uuid>", "titulo": "Programa 2025"}`
- **THEN** response is `201 Created` with `referencia_archivo: null`

#### Scenario: Create programa with duplicate materia × carrera × cohorte fails

- **WHEN** user calls `POST /api/programas` with `{"materia_id": "<uuid>", "carrera_id": "<uuid>", "cohorte_id": "<uuid>", "titulo": "Otro"}` and a programa with the same materia, carrera and cohorte already exists in the tenant
- **THEN** response is `409 Conflict` with `{"detail": "Ya existe un programa para esa materia, carrera y cohorte en este tenant"}`

#### Scenario: Create programa with extra fields fails

- **WHEN** user calls `POST /api/programas` with `{"materia_id": "<uuid>", "carrera_id": "<uuid>", "cohorte_id": "<uuid>", "titulo": "Test", "extra": "no-permitido"}`
- **THEN** response is `422 Unprocessable Entity` (extra fields forbidden by `extra='forbid'`)

### Requirement: System SHALL list all non-soft-deleted programas for the current tenant

The system SHALL return all non-soft-deleted programas for the current tenant, optionally filtered by `materia_id`, `carrera_id`, or `cohorte_id`.

#### Scenario: List programas returns tenant-scoped results

- **WHEN** user with `estructura:gestionar` calls `GET /api/programas`
- **THEN** response is `200 OK` with JSON array of programa objects
- **AND** each has `id`, `tenant_id`, `materia_id`, `carrera_id`, `cohorte_id`, `titulo`, `referencia_archivo`, `created_at`, `updated_at`
- **AND** no soft-deleted programas are included
- **AND** only programas from the current tenant are returned

#### Scenario: List programas filtered by materia

- **WHEN** user calls `GET /api/programas?materia_id=<uuid>`
- **THEN** response is `200 OK` with JSON array containing only programas for that materia

#### Scenario: List programas filtered by carrera

- **WHEN** user calls `GET /api/programas?carrera_id=<uuid>`
- **THEN** response is `200 OK` with JSON array containing only programas for that carrera

### Requirement: System SHALL return a single programa by id scoped to tenant

The system SHALL return a single programa by id, scoped to the current tenant.

#### Scenario: Get existing programa

- **WHEN** user calls `GET /api/programas/{programa_id}` for a valid programa
- **THEN** response is `200 OK` with the programa object

#### Scenario: Get non-existent programa returns 404

- **WHEN** user calls `GET /api/programas/{unknown_id}`
- **THEN** response is `404 Not Found` with `{"detail": "Programa no encontrado"}`

#### Scenario: Get programa from another tenant returns 404

- **WHEN** user of tenant A calls `GET /api/programas/{programa_id_from_tenant_B}`
- **THEN** response is `404 Not Found`

### Requirement: System SHALL update programa fields when user provides valid data

The system SHALL update programa fields (`titulo`, `referencia_archivo`) when user provides valid data. The combination `(materia_id, carrera_id, cohorte_id)` SHALL NOT be changeable — these are immutable after creation.

#### Scenario: Update programa titulo

- **WHEN** user calls `PATCH /api/programas/{programa_id}` with `{"titulo": "Nuevo titulo"}`
- **THEN** response is `200 OK` with updated programa
- **AND** `updated_at` is refreshed

#### Scenario: Update programa referencia_archivo

- **WHEN** user calls `PATCH /api/programas/{programa_id}` with `{"referencia_archivo": "/new/path/file.pdf"}`
- **THEN** response is `200 OK` with updated `referencia_archivo`

### Requirement: System SHALL soft-delete a programa without physical deletion

The system SHALL soft-delete a programa (set `deleted_at`) without physical deletion.

#### Scenario: Delete programa soft-deletes

- **WHEN** user calls `DELETE /api/programas/{programa_id}`
- **THEN** response is `204 No Content`
- **AND** `deleted_at` is set on the programa
- **AND** subsequent list queries do not return this programa

### Requirement: System SHALL deny access to programa endpoints for users without estructura:gestionar

The system SHALL deny access to programa endpoints for users without `estructura:gestionar` permission.

#### Scenario: Non-authorized user cannot list programas

- **WHEN** user WITHOUT `estructura:gestionar` calls `GET /api/programas`
- **THEN** response is `403 Forbidden`

#### Scenario: Non-authorized user cannot create programa

- **WHEN** user WITHOUT `estructura:gestionar` calls `POST /api/programas`
- **THEN** response is `403 Forbidden`
