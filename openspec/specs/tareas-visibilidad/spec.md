# tareas-visibilidad Specification

## Purpose
TBD - created by archiving change c-16-tareas-internas. Update Purpose after archive.
## Requirements
### Requirement: List mis tareas (docente)

The system SHALL allow a user with `tareas:gestionar` to list tareas assigned to them (where `asignado_a` is the authenticated user) with pagination and optional filters.

#### Scenario: PROFESOR lists their tareas
- **WHEN** a PROFESOR sends `GET /api/tareas/mis-tareas?page=1&per_page=20`
- **THEN** the system returns 200 with a paginated list of tareas where `asignado_a=<profesor_id>`

#### Scenario: PROFESOR filters mis tareas by estado
- **WHEN** a PROFESOR sends `GET /api/tareas/mis-tareas?estado=Pendiente`
- **THEN** the system returns 200 with only Pendiente tareas assigned to them

#### Scenario: PROFESOR filters mis tareas by materia
- **WHEN** a PROFESOR sends `GET /api/tareas/mis-tareas?materia_id=<uuid>`
- **THEN** the system returns 200 with only tareas for that materia assigned to them

#### Scenario: COORDINADOR lists mis tareas
- **WHEN** a COORDINADOR sends `GET /api/tareas/mis-tareas`
- **THEN** the system returns 200 with tareas assigned to them (COORDINADOR also has their own tasks)

### Requirement: List all tareas (admin view)

The system SHALL allow a user with `tareas:gestionar` who is COORDINADOR or ADMIN to list all tareas in the tenant with filters by docente asignado, docente asignador, materia, estado, and free text search.

#### Scenario: COORDINADOR lists all tareas
- **WHEN** a COORDINADOR sends `GET /api/tareas?page=1&per_page=20`
- **THEN** the system returns 200 with all tareas in the tenant (paginated)

#### Scenario: COORDINADOR filters by docente
- **WHEN** a COORDINADOR sends `GET /api/tareas?asignado_a=<uuid>`
- **THEN** the system returns 200 with only tareas assigned to that docente

#### Scenario: COORDINADOR filters by estado
- **WHEN** a COORDINADOR sends `GET /api/tareas?estado=En+progreso`
- **THEN** the system returns 200 with only tareas in En progreso

#### Scenario: COORDINADOR searches by text
- **WHEN** a COORDINADOR sends `GET /api/tareas?q=examen`
- **THEN** the system returns 200 with tareas where descripcion contains "examen"

#### Scenario: PROFESOR lists all tareas (scope violation)
- **WHEN** a PROFESOR sends `GET /api/tareas` (without /mis-tareas)
- **THEN** the system returns 403 Forbidden

