## ADDED Requirements

### Requirement: Student reserves a slot
The system SHALL allow an authenticated ALUMNO to reserve a day from available days with remaining cupos in an active convocation.

#### Scenario: Successful reservation
- **WHEN** ALUMNO calls `POST /api/coloquios/{evaluacion_id}/reservas` with {fecha}
- **AND** the fecha exists in dias array of the evaluacion
- **AND** cupos are available for that fecha (active reservas < cupos)
- **THEN** system creates ReservaEvaluacion with estado=Activa
- **AND** returns 201 with reserva_id and fecha_hora

#### Scenario: No cupos available
- **WHEN** ALUMNO tries to reserve a fecha that has reached cupos limit
- **THEN** system returns 409 Conflict with "Cupo agotado"

#### Scenario: Student already has active reservation
- **WHEN** ALUMNO calls `POST /api/coloquios/{evaluacion_id}/reservas` but already has an active reserva for this evaluacion
- **THEN** system returns 409 Conflict with "Ya possui una reserva activa"

#### Scenario: Fecha not in available days
- **WHEN** ALUMNO reserves a fecha not in the evaluacion's dias array
- **THEN** system returns 404 with "Fecha no disponible"

### Requirement: Student cancels own reservation
The system SHALL allow an ALUMNO to cancel their own active reservation.

#### Scenario: Cancel active reservation
- **WHEN** ALUMNO calls `PATCH /api/coloquios/reservas/{reserva_id}/cancelar`
- **AND** reserva belongs to the authenticated student
- **AND** reserva estado is Activa
- **THEN** system updates estado to Cancelada
- **AND** returns 200

#### Scenario: Cancel non-existent reservation
- **WHEN** ALUMNO calls `PATCH /api/coloquios/reservas/{reserva_id}/cancelar` for non-existent reserva
- **THEN** system returns 404

#### Scenario: Cancel reservation of another student
- **WHEN** ALUMNO calls `PATCH /api/coloquios/reservas/{reserva_id}/cancelar` for reserva belonging to another student
- **THEN** system returns 403 Forbidden

### Requirement: Student views own reservations
The system SHALL allow an ALUMNO to view their own reservations for all evaluations.

#### Scenario: List own reservations
- **WHEN** ALUMNO calls `GET /api/coloquios/mis-reservas`
- **THEN** system returns list of {reserva_id, evaluacion_id, materia, instancia, fecha_hora, estado}

### Requirement: Coordinator views all reservations for a convocation
The system SHALL allow COORDINADOR or ADMIN to view all reservations for a specific convocation.

#### Scenario: List reservations for convocation
- **WHEN** COORDINADOR calls `GET /api/coloquios/{evaluacion_id}/reservas`
- **THEN** system returns list of {reserva_id, alumno_id, alumno_nombre, fecha_hora, estado}

### Requirement: Coordinator records result for student
The system SHALL allow COORDINADOR or ADMIN to register a final grade for a student in an evaluation.

#### Scenario: Record result
- **WHEN** COORDINADOR calls `POST /api/coloquios/{evaluacion_id}/resultados` with {alumno_id, nota_final}
- **THEN** system creates or updates ResultadoEvaluacion entry
- **AND** returns 201 with resultado_id

#### Scenario: View consolidated results
- **WHEN** COORDINADOR calls `GET /api/coloquios/{evaluacion_id}/resultados`
- **THEN** system returns list of {alumno_id, alumno_nombre, nota_final, estado_reserva}