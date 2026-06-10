# fragmento-lms Specification

## Purpose
TBD - created by archiving change programas-y-fechas-academicas. Update Purpose after archive.
## Requirements
### Requirement: System SHALL generate an HTML fragment with fechas grouped by tipo for a given materia and cohorte

The system SHALL generate an HTML fragment containing all non-soft-deleted fechas academicas for the specified materia and cohorte, grouped by tipo (Parcial, TP, Coloquio), ordered by `numero_instancia` within each group.

#### Scenario: Generate fragment with multiple fechas

- **WHEN** user with `estructura:gestionar` calls `GET /api/fechas-academicas/fragmento-lms?materia_id=<uuid>&cohorte_id=<uuid>` and there are 3 fechas: Parcial #1 (2025-06-15), Parcial #2 (2025-07-20), TP #1 (2025-08-10)
- **THEN** response is `200 OK` with `Content-Type: text/html; charset=utf-8`
- **AND** the HTML body contains all three fechas
- **AND** fechas are grouped by tipo (Parcial section first, then TP)
- **AND** within each group, fechas are ordered by `numero_instancia`

#### Scenario: Generate fragment for materia with no fechas

- **WHEN** user calls `GET /api/fechas-academicas/fragmento-lms?materia_id=<uuid>&cohorte_id=<uuid>` and there are no fechas for that materia and cohorte
- **THEN** response is `200 OK` with an HTML fragment containing a message indicating no hay fechas registradas

#### Scenario: Generate fragment requires materia_id and cohorte_id

- **WHEN** user calls `GET /api/fechas-academicas/fragmento-lms` without `materia_id` or `cohorte_id`
- **THEN** response is `422 Unprocessable Entity` (missing required query parameters)

#### Scenario: Generate fragment excludes soft-deleted fechas

- **WHEN** user calls `GET /api/fechas-academicas/fragmento-lms?materia_id=<uuid>&cohorte_id=<uuid>` and a fecha for that materia was soft-deleted
- **THEN** the HTML fragment does NOT include the soft-deleted fecha

### Requirement: System SHALL include fecha titulo and descripcion in the fragment when present

The system SHALL include optional `titulo` and `descripcion` fields in the HTML fragment for each fecha when they are not null.

#### Scenario: Fragment includes titulo when present

- **WHEN** a fecha has `titulo: "Primer Parcial"` and `descripcion: "Unidades 1 a 4"`
- **THEN** the HTML fragment displays both titulo and descripcion for that fecha

#### Scenario: Fragment omits titulo section when null

- **WHEN** a fecha has `titulo: null`
- **THEN** the HTML fragment does not display a titulo for that fecha but still shows fecha and tipo

### Requirement: System SHALL deny access to fragmento-lms endpoint for users without estructura:gestionar

The system SHALL deny access to the fragmento-lms endpoint for users without `estructura:gestionar` permission.

#### Scenario: Non-authorized user cannot access fragmento-lms

- **WHEN** user WITHOUT `estructura:gestionar` calls `GET /api/fechas-academicas/fragmento-lms?materia_id=<uuid>&cohorte_id=<uuid>`
- **THEN** response is `403 Forbidden`

### Requirement: System SHALL scope fragmento-lms results to the current tenant only

The system SHALL only include fechas from the current tenant in the generated fragment. Fechas from other tenants SHALL NOT appear even if the same materia_id and cohorte_id exist in another tenant.

#### Scenario: Fragment scoped to current tenant

- **WHEN** user of tenant A calls `GET /api/fechas-academicas/fragmento-lms?materia_id=<shared_uuid>&cohorte_id=<shared_uuid>` and tenant B has fechas for the same materia_id and cohorte_id
- **THEN** the HTML fragment contains only fechas belonging to tenant A

