## ADDED Requirements

### Requirement: Users can log in with email, password, and tenant code

The system SHALL provide a login page with a form (React Hook Form + Zod) collecting `tenant_codigo`, `email`, and `password`. On submit it MUST call `POST /api/auth/login` through a `services/` hook. On a `200` response it MUST store the returned access token in memory, bootstrap the session, and navigate to the post-login destination. The identity and tenant of the session MUST come exclusively from the server response, never from the URL or any client-held value.

#### Scenario: Successful login stores the token and navigates in

- **WHEN** the user submits valid `tenant_codigo`, `email`, and `password` and `POST /api/auth/login` returns `200` with an access token (and `totp_enabled = false`)
- **THEN** the access token is stored in memory
- **AND** the session is bootstrapped
- **AND** the app navigates away from `/login` to the protected area

#### Scenario: Invalid credentials show a generic error

- **WHEN** `POST /api/auth/login` returns `401` with `code = "AUTH_INVALID_CREDENTIALS"`
- **THEN** the form shows a generic "credenciales inválidas" message
- **AND** the message does not reveal whether the email, password, or tenant was wrong

#### Scenario: Login form validates required fields before submitting

- **WHEN** the user submits the login form with an empty `email` or an invalid email format
- **THEN** the Zod validation blocks submission and shows field-level errors
- **AND** no `POST /api/auth/login` request is sent

### Requirement: 2FA step is required when the backend signals AUTH_2FA_REQUIRED

When `POST /api/auth/login` returns `401` with `code = "AUTH_2FA_REQUIRED"`, the UI MUST transition to a 2FA step that collects a 6-digit TOTP code and re-submits the login (or the documented verify endpoint) with the `totp_code`. A successful 2FA submission MUST complete the session bootstrap. An `AUTH_2FA_INVALID` response MUST keep the user on the 2FA step with a generic invalid-code message.

#### Scenario: Login with 2FA enrolled transitions to the 2FA step

- **WHEN** `POST /api/auth/login` returns `401` with `code = "AUTH_2FA_REQUIRED"`
- **THEN** the UI shows the 2FA code entry step
- **AND** no session is established yet

#### Scenario: Valid TOTP code completes login

- **WHEN** the user enters a valid 6-digit TOTP code and the re-submitted login returns `200` with an access token
- **THEN** the session is bootstrapped and the user is navigated into the protected area

#### Scenario: Invalid TOTP code keeps the user on the 2FA step

- **WHEN** the 2FA submission returns `401` with `code = "AUTH_2FA_INVALID"`
- **THEN** the user stays on the 2FA step with a generic "código inválido" message
- **AND** no session is established

### Requirement: Users can request a password reset and set a new password

The system SHALL provide a forgot-password page that collects `tenant_codigo` and `email` and calls `POST /api/auth/forgot`, and a reset page that reads the token, collects a new password (validated by Zod against the minimum length), and calls `POST /api/auth/reset`. The forgot page MUST always show the same neutral confirmation regardless of whether the email exists (no account enumeration). The reset page MUST surface expired/invalid-token outcomes without revealing user existence.

#### Scenario: Forgot-password always shows a neutral confirmation

- **WHEN** the user submits the forgot-password form and `POST /api/auth/forgot` returns `200`
- **THEN** the page shows a neutral "si el email existe, te enviamos instrucciones" message
- **AND** the message is identical whether or not the email is registered

#### Scenario: Reset with a valid token sets the new password and routes to login

- **WHEN** the user submits a new valid password on the reset page and `POST /api/auth/reset` returns `200`
- **THEN** a success message is shown and the user is routed to `/login`

#### Scenario: Reset with an expired or used token shows a recoverable error

- **WHEN** `POST /api/auth/reset` returns `401` with `code = "AUTH_RESET_EXPIRED"` or `"AUTH_RESET_INVALID"`
- **THEN** the page shows a "el enlace expiró o ya fue usado, solicitá uno nuevo" message
- **AND** offers a link back to the forgot-password flow

### Requirement: Users can log out and the session is cleared

The system SHALL provide a logout action that calls `POST /api/auth/logout`, clears the in-memory access token and the cached session, and navigates to `/login`. Logout MUST clear the local session even if the backend call fails (best-effort revocation).

#### Scenario: Logout clears the session and returns to login

- **WHEN** an authenticated user triggers logout and `POST /api/auth/logout` returns `204`
- **THEN** the in-memory access token and cached session are cleared
- **AND** the app navigates to `/login`

#### Scenario: Logout clears the local session even if the backend call fails

- **WHEN** the user triggers logout and `POST /api/auth/logout` errors
- **THEN** the in-memory access token and cached session are still cleared locally
- **AND** the app navigates to `/login`

### Requirement: The session is bootstrapped from the server, never from request data

After login, and on app start when a refresh token is available, the system SHALL bootstrap the session from the server (the session endpoint that returns the current user and effective permissions). The user identity, roles, and effective permissions MUST be read only from this server response. The client MUST NOT derive identity or permissions from URL parameters, form fields, or any client-held value.

#### Scenario: Session is populated from the server bootstrap response

- **WHEN** the session bootstrap request returns the current user and an array of effective permissions
- **THEN** the session state holds that user and those permissions
- **AND** the permissions used by the guard and menu come from this response only

#### Scenario: Identity in a URL parameter is ignored

- **WHEN** a URL contains a parameter such as `?user_id=<other>` 
- **THEN** the session identity is unchanged and remains the one from the server bootstrap
