# mensajeria-interna-rbac Specification

## Purpose

RBAC enforcement para mensajería interna. Extiende `mensajeria-interna` (C-20 archivado) agregando control de acceso basado en permisos `mensajes:enviar` y `mensajes:ver`. Anteriormente los endpoints solo requerían autenticación (`get_current_user`), permitiendo que cualquier usuario autenticado enviara o leyera mensajes de cualquier otro usuario del tenant.

## ADDED Requirements

### Requirement: Send message requires mensajes:enviar permission

The system SHALL only allow a user with `mensajes:enviar` permission to send a new internal message via `POST /api/mensajes`.

#### Scenario: User with permission can send message
- **WHEN** user with `mensajes:enviar` permission sends `POST /api/mensajes` with valid data
- **THEN** the system creates the message and returns 201

#### Scenario: User without permission gets 403
- **WHEN** user WITHOUT `mensajes:enviar` permission sends `POST /api/mensajes`
- **THEN** the system returns 403 Forbidden with `{"detail": "No tiene el permiso: mensajes:enviar"}`

#### Scenario: Unauthenticated request gets 401
- **WHEN** a request without valid JWT sends `POST /api/mensajes`
- **THEN** the system returns 401 Unauthorized

### Requirement: Reply to message requires mensajes:enviar permission

The system SHALL only allow a user with `mensajes:enviar` permission to reply to an existing message via `POST /api/mensajes/{mensaje_id}/reply`.

#### Scenario: User with permission can reply
- **WHEN** user with `mensajes:enviar` permission sends `POST /api/mensajes/{mensaje_id}/reply` with valid data
- **THEN** the system creates the reply and returns 201

#### Scenario: User without permission gets 403
- **WHEN** user WITHOUT `mensajes:enviar` permission sends `POST /api/mensajes/{mensaje_id}/reply`
- **THEN** the system returns 403 Forbidden with `{"detail": "No tiene el permiso: mensajes:enviar"}`

### Requirement: List inbox requires mensajes:ver permission

The system SHALL only allow a user with `mensajes:ver` permission to list their inbox via `GET /api/mensajes/inbox`.

#### Scenario: User with permission can list inbox
- **WHEN** user with `mensajes:ver` permission sends `GET /api/mensajes/inbox`
- **THEN** the system returns 200 with list of threads where user is participant

#### Scenario: User without permission gets 403
- **WHEN** user WITHOUT `mensajes:ver` permission sends `GET /api/mensajes/inbox`
- **THEN** the system returns 403 Forbidden with `{"detail": "No tiene el permiso: mensajes:ver"}`

### Requirement: Read thread requires mensajes:ver permission

The system SHALL only allow a user with `mensajes:ver` permission to read a message thread via `GET /api/mensajes/inbox/{hilo_id}`.

#### Scenario: User with permission can read thread
- **WHEN** user with `mensajes:ver` permission sends `GET /api/mensajes/inbox/{hilo_id}`
- **THEN** the system returns 200 with all messages in the thread and marks unread as read

#### Scenario: User without permission gets 403
- **WHEN** user WITHOUT `mensajes:ver` permission sends `GET /api/mensajes/inbox/{hilo_id}`
- **THEN** the system returns 403 Forbidden with `{"detail": "No tiene el permiso: mensajes:ver"}`

#### Scenario: User cannot read thread they are not part of
- **WHEN** user with `mensajes:ver` permission sends `GET /api/mensajes/inbox/{hilo_id}` where they are neither sender nor recipient
- **THEN** the system returns 404 (thread not visible)
