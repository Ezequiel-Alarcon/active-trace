# estructura-academica Specification

## ADDED Requirements

### Requirement: ABM Carreras
The system SHALL allow managing carreras (create, list, update, soft-delete) via the frontend, consuming C-06 backend APIs.

#### Scenario: Lists carreras in table
- **WHEN** a user with `estructura:gestionar` navigates to `/admin/estructura`
- **THEN** the system calls `GET /api/admin/carreras`
- **AND** shows a DataTable with columns: código, nombre, estado (StatusBadge: Activa/Inactiva), acciones (editar/eliminar)

#### Scenario: Create carrera via modal
- **WHEN** the user clicks "Agregar carrera"
- **THEN** a modal form opens with fields: código (text), nombre (text)
- **WHEN** submitted, the system calls `POST /api/admin/carreras`
- **AND** on success, the table refreshes

#### Scenario: Edit and soft-delete carrera
- **WHEN** the user edits a carrera, a pre-filled modal opens and calls `PATCH /api/admin/carreras/{id}`
- **WHEN** the user deletes, a confirmation dialog calls `DELETE /api/admin/carreras/{id}`

### Requirement: ABM Cohortes
The system SHALL allow managing cohortes within a carrera.

#### Scenario: Lists cohortes filtered by carrera
- **WHEN** the user switches to "Cohortes" tab and selects a carrera
- **THEN** the system calls `GET /api/admin/cohortes?carrera_id=<id>`
- **AND** shows a DataTable with columns: nombre, año, vig_desde, vig_hasta, estado, acciones

#### Scenario: CRUD operations for cohortes
- **WHEN** the user creates/edits/deletes cohortes
- **THEN** the same modal + confirmation flow as carreras applies
- **AND** endpoints are `POST /api/admin/cohortes`, `PATCH /api/admin/cohortes/{id}`, `DELETE /api/admin/cohortes/{id}`

### Requirement: ABM Materias
The system SHALL allow managing materias in the tenant's academic catalogue.

#### Scenario: Lists materias
- **WHEN** the user switches to "Materias" tab
- **THEN** the system calls `GET /api/admin/materias`
- **AND** shows a DataTable with columns: código, nombre, estado, acciones

#### Scenario: CRUD operations for materias
- **WHEN** the user creates/edits/deletes materias
- **THEN** the same modal + confirmation flow applies
- **AND** endpoints are `POST /api/admin/materias`, `PATCH /api/admin/materias/{id}`, `DELETE /api/admin/materias/{id}`
