# estructura-academica-materias Specification

## Purpose

Define el ABM del catálogo de materias. Materia es la entidad canónica del catálogo académico (ADR-006). La instancia de dictado (Materia × Carrera × Cohorte) se implementa en un change futuro. ADMIN puede crear, editar, listar, obtener y cambiar el estado de materias.

## ADDED Requirements

### Requirement: System SHALL create a new materia with unique codigo per tenant

The system SHALL create a new materia when ADMIN provides valid `codigo` and `nombre`. The `codigo` SHALL be unique within the tenant. The `estado` defaults to `Activa`.

#### Scenario: Create materia succeeds

- **WHEN** admin calls `POST /api/admin/materias` with `{"codigo": "MAT-101", "nombre": "Matematica Discreta"}`
- **THEN** response is `201 Created` with the created materia object
- **AND** `id` is a UUID
- **AND** `tenant_id` matches the current tenant from session
- **AND** `estado` is `Activa`
- **AND** `created_at` and `updated_at` are set

#### Scenario: Create materia with duplicate codigo fails

- **WHEN** admin calls `POST /api/admin/materias` with `{"codigo": "MAT-101"}` and a materia with codigo `MAT-101` already exists in the tenant
- **THEN** response is `409 Conflict` with `{"detail": "Ya existe una materia con ese codigo en este tenant"}`

### Requirement: System SHALL list all non-soft-deleted materias for the current tenant

The system SHALL return all non-soft-deleted materias for the current tenant, optionally filtered by `estado`.

#### Scenario: List materias returns tenant-scoped results

- **WHEN** admin calls `GET /api/admin/materias`
- **THEN** response is `200 OK` with JSON array of materia objects
- **AND** each has `id`, `tenant_id`, `codigo`, `nombre`, `estado`, `created_at`, `updated_at`
- **AND** no soft-deleted materias are included
- **AND** only materias from the current tenant are returned

#### Scenario: List materias filtered by estado

- **WHEN** admin calls `GET /api/admin/materias?estado=Inactiva`
- **THEN** response is `200 OK` with JSON array containing only materias where `estado == Inactiva`

### Requirement: System SHALL return a single materia by id

The system SHALL return a single materia by id, scoped to the current tenant.

#### Scenario: Get existing materia

- **WHEN** admin calls `GET /api/admin/materias/{materia_id}` for a valid materia
- **THEN** response is `200 OK` with the materia object

#### Scenario: Get non-existent materia returns 404

- **WHEN** admin calls `GET /api/admin/materias/{unknown_id}`
- **THEN** response is `404 Not Found` with `{"detail": "Materia no encontrada"}`

### Requirement: System SHALL update materia fields when admin provides valid data

The system SHALL update materia fields (codigo, nombre, estado) when admin provides valid data. Changing `codigo` to an existing one SHALL be rejected.

#### Scenario: Update materia nombre

- **WHEN** admin calls `PATCH /api/admin/materias/{materia_id}` with `{"nombre": "Analisis Matematico I"}`
- **THEN** response is `200 OK` with updated materia
- **AND** `updated_at` is refreshed

#### Scenario: Update materia to duplicate codigo fails

- **WHEN** admin calls `PATCH /api/admin/materias/{materia_id}` with `{"codigo": "MAT-201"}` and another materia already has codigo `MAT-201`
- **THEN** response is `409 Conflict`

### Requirement: System SHALL soft-delete a materia without physical deletion

The system SHALL soft-delete a materia.

#### Scenario: Delete materia soft-deletes

- **WHEN** admin calls `DELETE /api/admin/materias/{materia_id}`
- **THEN** response is `204 No Content`
- **AND** `deleted_at` is set on the materia
- **AND** subsequent list queries do not return this materia
