# fecha-academica-crud Specification

## Purpose

Define el ABM de fechas académicas. Cada fecha representa un evento evaluativo (parcial, TP o coloquio) para una materia en una cohorte específica, con un número de instancia que indica el orden (1er parcial, 2do parcial, etc.). ADMIN y COORDINADOR pueden crear, editar, consultar y soft-deletear fechas.

## ADDED Requirements

### Requirement: System SHALL create a new fecha academica with unique tipo × numero per materia × cohorte

The system SHALL create a new fecha academica when user provides valid `materia_id`, `cohorte_id`, `tipo`, `numero_instancia`, `fecha` and optional `titulo` and `descripcion`. The combination `(materia_id, cohorte_id, tipo, numero_instancia)` SHALL be unique within the tenant.

#### Scenario: Create fecha academica succeeds

- **WHEN** user with `estructura:gestionar` calls `POST /api/fechas-academicas` with `{"materia_id": "<uuid>", "cohorte_id": "<uuid>", "tipo": "Parcial", "numero_instancia": 1, "fecha": "2025-06-15", "titulo": "Primer Parcial", "descripcion": "Unidades 1 a 4"}`
- **THEN** response is `201 Created` with the created fecha object
- **AND** `id` is a UUID
- **AND** `tenant_id` matches the current tenant from session
- **AND** `tipo` is `Parcial`
- **AND** `created_at` and `updated_at` are set

#### Scenario: Create fecha academica with minimal fields succeeds

- **WHEN** user calls `POST /api/fechas-academicas` with `{"materia_id": "<uuid>", "cohorte_id": "<uuid>", "tipo": "TP", "numero_instancia": 1, "fecha": "2025-07-01"}`
- **THEN** response is `201 Created` with `titulo: null` and `descripcion: null`

#### Scenario: Create fecha with duplicate tipo × numero for same materia × cohorte fails

- **WHEN** user calls `POST /api/fechas-academicas` with `{"materia_id": "<uuid>", "cohorte_id": "<uuid>", "tipo": "Parcial", "numero_instancia": 1, "fecha": "2025-07-01"}` and a fecha with the same materia, cohorte, tipo and numero_instancia already exists
- **THEN** response is `409 Conflict` with `{"detail": "Ya existe una fecha de tipo Parcial #1 para esta materia y cohorte en este tenant"}`

#### Scenario: Create fecha with invalid tipo fails

- **WHEN** user calls `POST /api/fechas-academicas` with `{"materia_id": "<uuid>", "cohorte_id": "<uuid>", "tipo": "ExamenFinal", "numero_instancia": 1, "fecha": "2025-06-15"}`
- **THEN** response is `422 Unprocessable Entity` (invalid enum value)

#### Scenario: Create fecha with extra fields fails

- **WHEN** user calls `POST /api/fechas-academicas` with `{"materia_id": "<uuid>", "cohorte_id": "<uuid>", "tipo": "Parcial", "numero_instancia": 1, "fecha": "2025-06-15", "extra": "no-permitido"}`
- **THEN** response is `422 Unprocessable Entity` (extra fields forbidden by `extra='forbid'`)

### Requirement: System SHALL list all non-soft-deleted fechas academicas for the current tenant

The system SHALL return all non-soft-deleted fechas academicas for the current tenant, optionally filtered by `materia_id`, `cohorte_id`, or `tipo`.

#### Scenario: List fechas returns tenant-scoped results ordered by fecha

- **WHEN** user with `estructura:gestionar` calls `GET /api/fechas-academicas`
- **THEN** response is `200 OK` with JSON array of fecha objects ordered by `fecha` ascending
- **AND** each has `id`, `tenant_id`, `materia_id`, `cohorte_id`, `tipo`, `numero_instancia`, `fecha`, `titulo`, `descripcion`, `created_at`, `updated_at`
- **AND** no soft-deleted fechas are included
- **AND** only fechas from the current tenant are returned

#### Scenario: List fechas filtered by materia

- **WHEN** user calls `GET /api/fechas-academicas?materia_id=<uuid>`
- **THEN** response is `200 OK` with JSON array containing only fechas for that materia

#### Scenario: List fechas filtered by cohorte

- **WHEN** user calls `GET /api/fechas-academicas?cohorte_id=<uuid>`
- **THEN** response is `200 OK` with JSON array containing only fechas for that cohorte

#### Scenario: List fechas filtered by tipo

- **WHEN** user calls `GET /api/fechas-academicas?tipo=Parcial`
- **THEN** response is `200 OK` with JSON array containing only Parcial fechas

### Requirement: System SHALL return a single fecha academica by id scoped to tenant

The system SHALL return a single fecha academica by id, scoped to the current tenant.

#### Scenario: Get existing fecha

- **WHEN** user calls `GET /api/fechas-academicas/{fecha_id}` for a valid fecha
- **THEN** response is `200 OK` with the fecha object

#### Scenario: Get non-existent fecha returns 404

- **WHEN** user calls `GET /api/fechas-academicas/{unknown_id}`
- **THEN** response is `404 Not Found` with `{"detail": "Fecha academica no encontrada"}`

#### Scenario: Get fecha from another tenant returns 404

- **WHEN** user of tenant A calls `GET /api/fechas-academicas/{fecha_id_from_tenant_B}`
- **THEN** response is `404 Not Found`

### Requirement: System SHALL update fecha academica fields when user provides valid data

The system SHALL update fecha fields (`fecha`, `titulo`, `descripcion`) when user provides valid data. `tipo` and `numero_instancia` SHALL NOT be changeable — these are immutable after creation to preserve identity.

#### Scenario: Update fecha titulo and descripcion

- **WHEN** user calls `PATCH /api/fechas-academicas/{fecha_id}` with `{"titulo": "Nuevo titulo", "descripcion": "Nueva descripcion"}`
- **THEN** response is `200 OK` with updated fecha
- **AND** `updated_at` is refreshed

#### Scenario: Update fecha date

- **WHEN** user calls `PATCH /api/fechas-academicas/{fecha_id}` with `{"fecha": "2025-07-15"}`
- **THEN** response is `200 OK` with updated `fecha`

#### Scenario: Attempt to change tipo fails

- **WHEN** user calls `PATCH /api/fechas-academicas/{fecha_id}` with `{"tipo": "Coloquio"}` and the fecha was originally `Parcial`
- **THEN** response is `422 Unprocessable Entity` with detail indicating tipo is immutable

### Requirement: System SHALL soft-delete a fecha academica without physical deletion

The system SHALL soft-delete a fecha academica (set `deleted_at`) without physical deletion.

#### Scenario: Delete fecha soft-deletes

- **WHEN** user calls `DELETE /api/fechas-academicas/{fecha_id}`
- **THEN** response is `204 No Content`
- **AND** `deleted_at` is set on the fecha
- **AND** subsequent list queries do not return this fecha

### Requirement: System SHALL deny access to fecha academica endpoints for users without estructura:gestionar

The system SHALL deny access to fecha academica endpoints for users without `estructura:gestionar` permission.

#### Scenario: Non-authorized user cannot list fechas

- **WHEN** user WITHOUT `estructura:gestionar` calls `GET /api/fechas-academicas`
- **THEN** response is `403 Forbidden`

#### Scenario: Non-authorized user cannot create fecha

- **WHEN** user WITHOUT `estructura:gestionar` calls `POST /api/fechas-academicas`
- **THEN** response is `403 Forbidden`
