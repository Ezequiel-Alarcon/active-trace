# tareas-crud Specification

## Purpose
TBD - created by archiving change c-16-tareas-internas. Update Purpose after archive.
## Requirements
### Requirement: Create tarea

The system SHALL allow a user with `tareas:gestionar` permission to create a tarea with: materia_id (opcional), asignado_a (UUID del usuario destino), descripcion, contexto_id (opcional). The tarea is tenant-scoped via the authenticated user's tenant. The `asignado_por` is set to the authenticated user. Default estado is `Pendiente`.

#### Scenario: COORDINADOR creates a tarea for a docente
- **WHEN** a COORDINADOR sends `POST /api/tareas` with `asignado_a=<docente_id>`, `descripcion="Revisar planificacion"`
- **THEN** the system creates the tarea with `estado=Pendiente`, `asignado_por=<coordinador_id>` and returns 201

#### Scenario: PROFESOR creates a tarea for themselves
- **WHEN** a PROFESOR sends `POST /api/tareas` with `asignado_a=<propio_id>`, `descripcion="Preparar examen"`
- **THEN** the system creates the tarea and returns 201

#### Scenario: PROFESOR creates a tarea for otro docente (scope violation)
- **WHEN** a PROFESOR sends `POST /api/tareas` with `asignado_a=<otro_docente_id>`
- **THEN** the system returns 403 Forbidden (PROFESOR solo puede crear tareas propias)

#### Scenario: Create tarea without gestionar permission
- **WHEN** an ALUMNO sends `POST /api/tareas`
- **THEN** the system returns 403 Forbidden

#### Scenario: Create tarea with invalid data
- **WHEN** user sends `POST /api/tareas` without `descripcion`
- **THEN** the system returns 422 with validation error

### Requirement: Read tarea

The system SHALL allow a user with `tareas:gestionar` to retrieve a tarea by ID within their tenant. PROFESOR can only read tareas where they are the assignee; COORDINADOR/ADMIN can read any.

#### Scenario: COORDINADOR reads any tarea
- **WHEN** a COORDINADOR sends `GET /api/tareas/{id}`
- **THEN** the system returns 200 with the tarea data

#### Scenario: PROFESOR reads their own tarea
- **WHEN** a PROFESOR sends `GET /api/tareas/{id}` where `asignado_a` is the PROFESOR
- **THEN** the system returns 200 with the tarea data

#### Scenario: PROFESOR reads another's tarea
- **WHEN** a PROFESOR sends `GET /api/tareas/{id}` where `asignado_a` is NOT the PROFESOR
- **THEN** the system returns 404

#### Scenario: Read non-existent tarea
- **WHEN** user sends `GET /api/tareas/{non_existent_id}`
- **THEN** the system returns 404

### Requirement: Update tarea estado

The system SHALL allow a user with `tareas:gestionar` to update the `estado` of a tarea. PROFESOR can only update their own tareas. Allowed transitions: Pendiente→En progreso, Pendiente→Cancelada, En progreso→Resuelta, En progreso→Cancelada.

#### Scenario: PROFESOR marks tarea as En progreso
- **WHEN** a PROFESOR sends `PATCH /api/tareas/{id}` with `{"estado": "En progreso"}` on their own tarea
- **THEN** the system updates the tarea and returns 200

#### Scenario: PROFESOR marks tarea as Resuelta
- **WHEN** a PROFESOR sends `PATCH /api/tareas/{id}` with `{"estado": "Resuelta"}` on their own tarea in `En progreso`
- **THEN** the system updates and returns 200

#### Scenario: COORDINADOR updates any tarea
- **WHEN** a COORDINADOR sends `PATCH /api/tareas/{id}` with `{"estado": "Cancelada"}`
- **THEN** the system updates and returns 200 regardless of assignee

#### Scenario: PROFESOR updates another's tarea
- **WHEN** a PROFESOR sends `PATCH /api/tareas/{id}` where tarea belongs to another docente
- **THEN** the system returns 404

#### Scenario: Invalid state transition
- **WHEN** user sends `PATCH /api/tareas/{id}` with `{"estado": "Pendiente"}` on a `Resuelta` tarea
- **THEN** the system returns 400 with validation error

### Requirement: Soft-delete tarea

The system SHALL soft-delete a tarea when a COORDINADOR/ADMIN sends DELETE. PROFESOR cannot delete tareas.

#### Scenario: COORDINADOR deletes tarea
- **WHEN** a COORDINADOR sends `DELETE /api/tareas/{id}`
- **THEN** the system sets `deleted_at` and returns 204

#### Scenario: PROFESOR attempts to delete tarea
- **WHEN** a PROFESOR sends `DELETE /api/tareas/{id}`
- **THEN** the system returns 403 Forbidden

