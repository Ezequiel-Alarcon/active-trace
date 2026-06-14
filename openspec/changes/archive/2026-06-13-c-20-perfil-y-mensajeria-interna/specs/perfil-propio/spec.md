## ADDED Requirements

### Requirement: Authenticated user reads own profile
The system SHALL expose a `GET /api/perfil` endpoint that returns the authenticated user's profile data, including all non-PII fields and decrypted PII fields.

#### Scenario: Successful profile read
- **WHEN** any authenticated user sends `GET /api/perfil`
- **THEN** the system returns HTTP 200 with the user's `id`, `tenant_id`, `nombre`, `apellidos`, `email`, `dni`, `cuil`, `cbu`, `alias_cbu`, `banco`, `regional`, `legajo`, `legajo_profesional`, `fecha_nacimiento`, `genero`, `observaciones`, `created_at`, `updated_at`

#### Scenario: Unauthenticated request is rejected
- **WHEN** a request without a valid JWT sends `GET /api/perfil`
- **THEN** the system returns HTTP 401

### Requirement: Authenticated user edits own profile
The system SHALL expose a `PATCH /api/perfil` endpoint that lets authenticated users update editable fields on their own profile. `cuil` SHALL NOT be present in the request schema.

#### Scenario: Successful partial profile update
- **WHEN** an authenticated user sends `PATCH /api/perfil` with `{"nombre": "Nuevo nombre", "banco": "Nuevo banco"}`
- **THEN** the system returns HTTP 200 with the updated profile data, and only the supplied fields are modified

#### Scenario: cuil is rejected silently
- **WHEN** an authenticated user sends `PATCH /api/perfil` with a body containing `cuil`
- **THEN** the system returns HTTP 422 (validation error — `cuil` not a recognized field)

#### Scenario: Empty update succeeds
- **WHEN** an authenticated user sends `PATCH /api/perfil` with empty body `{}`
- **THEN** the system returns HTTP 200 with no changes (idempotent)

#### Scenario: Unauthenticated update is rejected
- **WHEN** a request without a valid JWT sends `PATCH /api/perfil`
- **THEN** the system returns HTTP 401

### Requirement: PII fields are re-encrypted on write
When a user updates PII fields (`email`, `dni`, `cbu`, `alias_cbu`), the system SHALL encrypt the new value using AES-256 before persisting.

#### Scenario: Email update triggers re-encryption
- **WHEN** a user updates their `email` via `PATCH /api/perfil`
- **THEN** the stored `email_enc` column contains a value different from the plaintext, and a subsequent `GET /api/perfil` returns the new plaintext email

### Requirement: Profile read returns data for the authenticated user only
The `GET /api/perfil` endpoint SHALL resolve the user identity exclusively from the JWT, never from path/query/body parameters.

#### Scenario: User reads own profile
- **WHEN** user with JWT for user_A sends `GET /api/perfil`
- **THEN** the response contains user_A's data

#### Scenario: Path parameter is ignored
- **WHEN** user_A sends `GET /api/perfil?user_id=user_B`
- **THEN** the response STILL contains user_A's data (the `user_id` parameter is ignored)
