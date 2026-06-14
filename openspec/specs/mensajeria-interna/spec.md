# mensajeria-interna Specification

## Purpose
TBD - created by archiving change c-20-perfil-y-mensajeria-interna. Update Purpose after archive.
## Requirements
### Requirement: Send a new internal message
The system SHALL expose a `POST /api/mensajes` endpoint that lets any authenticated user send a new internal message to another registered user within the same tenant. The message MUST specify `asunto`, `cuerpo`, and `destinatario_id`. When no `hilo_id` is provided, a new thread is started (the new message's `id` becomes the `hilo_id`).

#### Scenario: Send new message starts a thread
- **WHEN** user_A sends `POST /api/mensajes` with `{"asunto": "Revisión", "cuerpo": "Hola, revisa esto", "destinatario_id": "<user_B_id>"}`
- **THEN** the system returns HTTP 201 with the created message, and the response includes a `hilo_id` equal to the new message's `id`

#### Scenario: Send to non-existent user fails
- **WHEN** user_A sends `POST /api/mensajes` with a `destinatario_id` that does not exist
- **THEN** the system returns HTTP 404

#### Scenario: Unauthenticated send is rejected
- **WHEN** a request without a valid JWT sends `POST /api/mensajes`
- **THEN** the system returns HTTP 401

### Requirement: Reply within an existing thread
The system SHALL expose a `POST /api/mensajes/{mensaje_id}/reply` endpoint that lets any authenticated user reply to an existing message within the same thread.

#### Scenario: Reply extends thread
- **WHEN** user_B sends `POST /api/mensajes/{parent_id}/reply` with `{"asunto": "RE: Revisión", "cuerpo": "Gracias, lo reviso"}`
- **THEN** the system returns HTTP 201 with the reply, where `padre_id` equals `parent_id`, `hilo_id` matches the parent's `hilo_id`, and `destinatario_id` is the original sender

#### Scenario: Reply to non-existent message fails
- **WHEN** any user sends a reply to a `mensaje_id` that does not exist
- **THEN** the system returns HTTP 404

### Requirement: List inbox threads
The system SHALL expose a `GET /api/mensajes/inbox` endpoint that returns all active threads (most recent message per thread) where the authenticated user is either the recipient or the sender, ordered by most recent activity descending.

#### Scenario: Inbox shows threads for recipient
- **WHEN** user_B sends `GET /api/mensajes/inbox`
- **THEN** the system returns HTTP 200 with a list of threads where user_B is `destinatario_id` or `remitente_id`, each showing the latest message and whether it has been read

### Requirement: Read a thread's messages
The system SHALL expose a `GET /api/mensajes/inbox/{hilo_id}` endpoint that returns all messages in a thread, ordered by `created_at` ascending. When the authenticated user is the recipient, all unread messages in the thread SHALL have their `leido_at` set to the current timestamp.

#### Scenario: Read thread marks messages as read
- **WHEN** user_B sends `GET /api/mensajes/inbox/{hilo_id}` for a thread containing messages from user_A addressed to user_B
- **THEN** the system returns HTTP 200 with all messages, and the previously unread messages have `leido_at` populated

#### Scenario: Read thread scoped to own messages
- **WHEN** user_A sends `GET /api/mensajes/inbox/{hilo_id}` for a thread where user_A is neither `remitente_id` nor `destinatario_id` on any message
- **THEN** the system returns HTTP 404 (thread not visible to user_A)

### Requirement: Messages are tenant-scoped
All internal messages SHALL inherit `TenantScopedMixin`, ensuring automatic tenant isolation. Users cannot send or read messages across tenant boundaries.

#### Scenario: Cross-tenant message blocked
- **WHEN** user_A (tenant_1) sends a message to user_B (tenant_2)
- **THEN** a 404 is raised because user_B is not found in tenant_1's scope

