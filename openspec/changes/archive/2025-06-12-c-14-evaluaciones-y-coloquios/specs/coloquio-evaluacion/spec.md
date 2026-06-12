## ADDED Requirements

### Requirement: Coordinator creates evaluation convocation
The system SHALL allow COORDINADOR or ADMIN to create an evaluation convocation with materia, instance name, start date, number of days, and cupos per day.

#### Scenario: Successful convocation creation
- **WHEN** COORDINADOR calls `POST /api/coloquios` with materia_id, instancia, fecha_inicio, dias_disponibles, cupos
- **THEN** system creates Evaluacion record with dias JSONB array auto-populated with N date entries
- **AND** returns 201 with evaluacion_id and dias array

#### Scenario: Convocation with invalid materia
- **WHEN** COORDINADOR creates convocation with non-existent materia_id
- **THEN** system returns 404 with error detail

### Requirement: Coordinator imports students to convocation
The system SHALL allow COORDINADOR or ADMIN to import a list of student IDs to an existing convocation.

#### Scenario: Import students to active convocation
- **WHEN** COORDINADOR calls `POST /api/coloquios/{evaluacion_id}/importar` with list of alumno_ids
- **THEN** system validates each alumno exists and is ALUMNO role
- **AND** creates ResultadoEvaluacion entries with null nota_final for each valid student
- **AND** returns count of imported and skipped (already exists)

#### Scenario: Import to non-existent convocation
- **WHEN** COORDINADOR imports to non-existent evaluacion_id
- **THEN** system returns 404

### Requirement: Coordinator lists all convocations
The system SHALL return a paginated list of all evaluacion records for the tenant with computed metrics.

#### Scenario: List convocations with metrics
- **WHEN** COORDINADOR calls `GET /api/coloquios`
- **THEN** system returns list of {id, materia, instancia, fecha_inicio, dias, state, metrics: {convocados, reservas_activas, cupos_libres}}

#### Scenario: Empty list when no convocations
- **WHEN** COORDINADOR calls `GET /api/coloquios` with no records
- **THEN** system returns empty list with 200

### Requirement: Coordinator views metrics panel
The system SHALL expose aggregated metrics across all active evaluation sessions.

#### Scenario: Metrics panel returns aggregated data
- **WHEN** COORDINADOR calls `GET /api/coloquios/metricas`
- **THEN** system returns {total_convocados, total_reservas_activas, total_cupos_libres, instancias_activas}

### Requirement: Coordinator closes convocation
The system SHALL allow COORDINADOR or ADMIN to close a convocation (no more reservations allowed).

#### Scenario: Close convocation
- **WHEN** COORDINADOR calls `PATCH /api/coloquios/{evaluacion_id}/cerrar`
- **THEN** evaluacion estado changes to Cerrada
- **AND** further reservation attempts return 400