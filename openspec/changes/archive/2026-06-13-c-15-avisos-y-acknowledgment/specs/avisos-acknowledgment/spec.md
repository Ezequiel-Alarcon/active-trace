# avisos-acknowledgment Specification

## ADDED Requirements

### Requirement: User acknowledges an aviso

The system SHALL allow an authenticated user to acknowledge an aviso that has `requiere_ack=true` by sending `POST /api/avisos/{id}/acknowledge`. This creates an immutable AcknowledgmentAviso record. A user SHALL NOT acknowledge the same aviso twice.

#### Scenario: User acknowledges an aviso successfully
- **WHEN** an authenticated user sends `POST /api/avisos/{id}/acknowledge` for an aviso with `requiere_ack=true` that they haven't acknowledged before
- **THEN** the system creates an AcknowledgmentAviso record with the current timestamp and returns 201

#### Scenario: User acknowledges same aviso twice
- **WHEN** an authenticated user sends `POST /api/avisos/{id}/acknowledge` for an aviso they already acknowledged
- **THEN** the system returns 409 Conflict with `{"detail": "Ya confirmó este aviso"}`

#### Scenario: User acknowledges an aviso that doesn't require ack
- **WHEN** an authenticated user sends `POST /api/avisos/{id}/acknowledge` for an aviso with `requiere_ack=false`
- **THEN** the system returns 400 Bad Request with `{"detail": "Este aviso no requiere confirmación"}`

#### Scenario: Unauthenticated user acknowledges
- **WHEN** a request without valid JWT sends `POST /api/avisos/{id}/acknowledge`
- **THEN** the system returns 401 Unauthorized

### Requirement: Acknowledgment counter

The system SHALL provide an endpoint `GET /api/avisos/{id}/acknowledgment` that returns whether the current user has acknowledged and the total count of acknowledgments for the aviso.

#### Scenario: Get acknowledgment status for an aviso
- **WHEN** an authenticated user sends `GET /api/avisos/{id}/acknowledgment` for an aviso with 5 acknowledgments, and this user is among them
- **THEN** the system returns 200 with `{"total": 5, "user_acknowledged": true, "requiere_ack": true}`

#### Scenario: Get acknowledgment status without user ack
- **WHEN** an authenticated user sends `GET /api/avisos/{id}/acknowledgment` for an aviso with 3 acknowledgments, and this user is NOT among them
- **THEN** the system returns 200 with `{"total": 3, "user_acknowledged": false, "requiere_ack": true}`

#### Scenario: Get acknowledgment status for non-ack aviso
- **WHEN** an authenticated user sends `GET /api/avisos/{id}/acknowledgment` for an aviso with `requiere_ack=false`
- **THEN** the system returns 200 with `{"total": 0, "user_acknowledged": false, "requiere_ack": false}`
