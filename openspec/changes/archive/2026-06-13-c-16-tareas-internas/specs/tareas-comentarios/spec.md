## ADDED Requirements

### Requirement: Create comentario on tarea

The system SHALL allow a user with `tareas:gestionar` to add a comment to a tarea. PROFESOR can only comment on their own tareas; COORDINADOR/ADMIN can comment on any. The `autor_id` is set to the authenticated user.

#### Scenario: COORDINADOR adds comment to tarea
- **WHEN** a COORDINADOR sends `POST /api/tareas/{id}/comentarios` with `{"texto": "Revisado, corregir fechas"}`
- **THEN** the system creates the comment with `autor_id=<coordinador_id>` and returns 201

#### Scenario: PROFESOR adds comment to own tarea
- **WHEN** a PROFESOR sends `POST /api/tareas/{id}/comentarios` with `{"texto": "Listo para revisión"}` on their own tarea
- **THEN** the system creates the comment and returns 201

#### Scenario: PROFESOR adds comment to another's tarea
- **WHEN** a PROFESOR sends `POST /api/tareas/{id}/comentarios` on a tarea assigned to another docente
- **THEN** the system returns 404

#### Scenario: Add comment to non-existent tarea
- **WHEN** user sends `POST /api/tareas/{non_existent_id}/comentarios`
- **THEN** the system returns 404

#### Scenario: Add comment with empty texto
- **WHEN** user sends `POST /api/tareas/{id}/comentarios` with `{"texto": ""}`
- **THEN** the system returns 422

### Requirement: List comentarios on tarea

The system SHALL return all comments for a tarea ordered by `creado_at` ascending, paginated. Same scope rules apply.

#### Scenario: COORDINADOR lists comments of any tarea
- **WHEN** a COORDINADOR sends `GET /api/tareas/{id}/comentarios?page=1&per_page=20`
- **THEN** the system returns 200 with a paginated list of comments

#### Scenario: PROFESOR lists comments of own tarea
- **WHEN** a PROFESOR sends `GET /api/tareas/{id}/comentarios` on their own tarea
- **THEN** the system returns 200 with comments

#### Scenario: PROFESOR lists comments of another's tarea
- **WHEN** a PROFESOR sends `GET /api/tareas/{id}/comentarios` on a tarea assigned to another docente
- **THEN** the system returns 404
