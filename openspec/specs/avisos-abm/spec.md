# avisos-abm Specification

## Purpose
TBD - created by archiving change c-15-avisos-y-acknowledgment. Update Purpose after archive.
## Requirements
### Requirement: Create aviso

The system SHALL allow a user with `avisos:publicar` permission to create an aviso with: titulo, cuerpo, alcance (Global|PorMateria|PorCohorte|PorRol), severidad (Info|Advertencia|Crítico), opcionalmente rol_destino, materia_id, cohorte_id, inicio_en, fin_en, orden, activo, requiere_ack. The aviso is tenant-scoped via the authenticated user's tenant.

#### Scenario: COORDINADOR creates a global aviso
- **WHEN** a COORDINADOR sends `POST /api/avisos` with `alcance=Global`, `severidad=Info`, `titulo="Feriado 25 de Mayo"`, `inicio_en` and `fin_en` in the future, `requiere_ack=false`
- **THEN** the system creates the aviso and returns 201 with the aviso data

#### Scenario: ADMIN creates a PorRol aviso with severity Crítico
- **WHEN** an ADMIN sends `POST /api/avisos` with `alcance=PorRol`, `rol_destino=PROFESOR`, `severidad=Crítico`, `requiere_ack=true`
- **THEN** the system creates the aviso and returns 201

#### Scenario: Create aviso without publicar permission
- **WHEN** an ALUMNO sends `POST /api/avisos`
- **THEN** the system returns 403 Forbidden

#### Scenario: Create aviso with invalid data
- **WHEN** user sends `POST /api/avisos` without `titulo`
- **THEN** the system returns 422 with validation error

### Requirement: Read aviso

The system SHALL allow a user with `avisos:publicar` to retrieve any aviso by ID within their tenant.

#### Scenario: COORDINADOR reads an aviso by ID
- **WHEN** a COORDINADOR sends `GET /api/avisos/{id}`
- **THEN** the system returns 200 with the aviso data

#### Scenario: Read non-existent aviso
- **WHEN** a user sends `GET /api/avisos/{non_existent_id}`
- **THEN** the system returns 404

### Requirement: Update aviso

The system SHALL allow a user with `avisos:publicar` to update any field of an aviso within their tenant. Partial updates are supported via PATCH.

#### Scenario: COORDINADOR updates aviso titulo
- **WHEN** a COORDINADOR sends `PATCH /api/avisos/{id}` with `{"titulo": "Nuevo título"}`
- **THEN** the system updates the aviso and returns 200 with the updated data

#### Scenario: Update aviso in another tenant
- **WHEN** a COORDINADOR from tenant A sends `PATCH /api/avisos/{id}` where the aviso belongs to tenant B
- **THEN** the system returns 404 (tenant isolation)

### Requirement: Soft-delete aviso

The system SHALL soft-delete an aviso when a user with `avisos:publicar` sends DELETE. The record is not physically removed; `deleted_at` is set.

#### Scenario: COORDINADOR deletes aviso
- **WHEN** a COORDINADOR sends `DELETE /api/avisos/{id}`
- **THEN** the system sets `deleted_at` on the aviso and returns 204

### Requirement: List avisos for management

The system SHALL allow a user with `avisos:publicar` to list all avisos in their tenant (including inactive and expired) with pagination.

#### Scenario: COORDINADOR lists all avisos
- **WHEN** a COORDINADOR sends `GET /api/avisos?page=1&per_page=20`
- **THEN** the system returns 200 with a paginated list of all avisos in the tenant

#### Scenario: COORDINADOR filters avisos by alcance
- **WHEN** a COORDINADOR sends `GET /api/avisos?alcance=Global`
- **THEN** the system returns 200 with only avisos where alcance=Global

