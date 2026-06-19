## ADDED Requirements

### Requirement: The system authenticates users with email, password, and optional TOTP

The system SHALL expose `POST /api/auth/login` that accepts `{tenant_codigo, email, password, totp_code?}`. The service MUST resolve the tenant by `codigo` (404/401 if missing, soft-deleted, or `estado = Inactivo`, surfaced as a generic `AUTH_INVALID_CREDENTIALS` to avoid leaking tenant existence). It MUST load the `auth_user` row, verify the Argon2id password hash, and:

- If the password is invalid → respond `401` with `code = "AUTH_INVALID_CREDENTIALS"`, increment `failed_login_count`, emit `AUTH_LOGIN_FAIL` with `email_hash` (SHA-256 lowercased email) and `tenant_id_hash` (no plaintext), and return.
- If the password is valid and `totp_enabled = false` → issue an access token and a refresh token (both signed JWTs), create a new `auth_session` row, emit `AUTH_LOGIN_OK`, and return `{access_token, refresh_token, token_type: "Bearer", expires_in: 900}`.
- If the password is valid and `totp_enabled = true` and `totp_code` is missing → respond `401` with `code = "AUTH_2FA_REQUIRED"`, do not create a session, do not emit `AUTH_LOGIN_OK`.
- If the password is valid and `totp_enabled = true` and `totp_code` is present → verify the TOTP code against the decrypted `totp_secret_enc` with `valid_window=1`. On match → issue tokens, create a session, emit `AUTH_LOGIN_OK`. On mismatch → respond `401` with `code = "AUTH_2FA_INVALID"`, do not create a session, emit `AUTH_LOGIN_FAIL`.

The `tenant_codigo` is the only tenant hint the client provides; identity and tenant on the resulting tokens come exclusively from the verified credential lookup.

#### Scenario: Login with valid credentials and no 2FA returns an access and refresh token

- **WHEN** a `POST /api/auth/login` is sent with `{tenant_codigo: "UBA_FCEN", email: "alice@example.com", password: "correct-horse-battery-staple"}` and the user exists, is active, has no 2FA, and the password verifies
- **THEN** the response is `200` with a JSON body containing a JWT `access_token`, a JWT `refresh_token`, `token_type: "Bearer"`, and `expires_in: 900`
- **AND** a new `auth_session` row exists for that user with `revoked_at IS NULL`
- **AND** an audit event with action `AUTH_LOGIN_OK` has been emitted

#### Scenario: Login with wrong password returns 401 and does not create a session

- **WHEN** a `POST /api/auth/login` is sent with a wrong password for an existing user
- **THEN** the response is `401` with `code = "AUTH_INVALID_CREDENTIALS"`
- **AND** no `auth_session` row is created
- **AND** an audit event with action `AUTH_LOGIN_FAIL` is emitted, with `email_hash` and `tenant_id_hash` but no plaintext email or password

#### Scenario: Login for a soft-deleted or inactive user returns the same 401 as a wrong password

- **WHEN** a `POST /api/auth/login` is sent for a user that is soft-deleted (`deleted_at IS NOT NULL`) or `is_active = false`
- **THEN** the response is `401` with `code = "AUTH_INVALID_CREDENTIALS"` (the same code as a wrong password)
- **AND** no `auth_session` row is created
- **AND** no information about the user's status leaks in the response body

#### Scenario: Login for a non-existent tenant returns the same 401 and constant-time

- **WHEN** a `POST /api/auth/login` is sent with `tenant_codigo` that does not exist (or the tenant is soft-deleted or `estado = Inactivo`)
- **THEN** the response is `401` with `code = "AUTH_INVALID_CREDENTIALS"`
- **AND** the response time is within `±50ms` of the response time for a wrong-password attempt against an existing tenant (no tenant-existence timing leak)

#### Scenario: Login with 2FA enrolled but no TOTP code returns 401 AUTH_2FA_REQUIRED

- **WHEN** a `POST /api/auth/login` is sent with valid credentials for a user that has `totp_enabled = true` and no `totp_code` in the body
- **THEN** the response is `401` with `code = "AUTH_2FA_REQUIRED"`
- **AND** no `auth_session` row is created
- **AND** no `AUTH_LOGIN_OK` is emitted

#### Scenario: Login with valid credentials and a valid TOTP code issues tokens

- **WHEN** a `POST /api/auth/login` is sent with valid credentials and a 6-digit `totp_code` matching the user's TOTP secret within `valid_window=1`
- **THEN** the response is `200` with `access_token`, `refresh_token`, `token_type: "Bearer"`, `expires_in: 900`
- **AND** an `auth_session` row is created
- **AND** an audit event with action `AUTH_LOGIN_OK` is emitted

#### Scenario: Login with valid credentials and an invalid TOTP code returns 401 AUTH_2FA_INVALID

- **WHEN** a `POST /api/auth/login` is sent with valid credentials and a `totp_code` that does not verify
- **THEN** the response is `401` with `code = "AUTH_2FA_INVALID"`
- **AND** no `auth_session` row is created
- **AND** an audit event with action `AUTH_LOGIN_FAIL` is emitted

### Requirement: The system issues a short-lived access token and a DB-backed refresh token

The access token MUST be a JWT signed with `Settings.SECRET_KEY` (HS256), with claims `sub` (the user's UUID, as a string), `tid` (the tenant UUID, as a string), `sid` (the session UUID, as a string), `iat`, `exp`, `jti` (UUID), and `typ: "access"`. The access token MUST expire `ACCESS_TOKEN_EXPIRE_MINUTES` (default 15) after `iat`.

The refresh token MUST be a JWT with the same signing key and the same claims, plus `typ: "refresh"`. The refresh token's `jti` MUST match the `jti` of the corresponding `auth_session` row. The `auth_session` row MUST store an Argon2id hash of the refresh token string in `refresh_token_hash`; the raw refresh token is never persisted. The refresh token MUST expire `REFRESH_TOKEN_EXPIRE_MINUTES` (default `60 * 24 * 7`) after `iat`.

The service MUST NOT include roles or permissions in either token. The `tid` claim MUST equal the `tenant_id` of the loaded `auth_user` row.

#### Scenario: Access token is a signed JWT with the documented claims

- **WHEN** a successful login completes
- **THEN** the returned `access_token` is a JWT whose header is `{"alg": "HS256", "typ": "JWT"}`
- **AND** whose payload contains `sub` (the user's UUID as a string), `tid` (the tenant's UUID as a string), `sid` (the new session's UUID as a string), `iat`, `exp`, `jti` (a UUID), and `typ: "access"`
- **AND** the token verifies with `Settings.SECRET_KEY`

#### Scenario: Refresh token is a signed JWT whose jti matches the new session row

- **WHEN** a successful login completes
- **THEN** the returned `refresh_token` is a JWT with the same signing key, `typ: "refresh"`, `jti` matching the `auth_session.jti`, and `exp` = `iat + REFRESH_TOKEN_EXPIRE_MINUTES`
- **AND** the `auth_session.refresh_token_hash` equals the Argon2id hash of the refresh token string

#### Scenario: Tokens carry no roles or permissions

- **WHEN** any token is decoded
- **THEN** it has no claim that looks like a role name (`roles`, `role`, `perms`, `permissions`)
- **AND** any attempt by the auth service to include such a claim is rejected in code review (the schema check rejects unknown fields)

### Requirement: Refresh token rotation revokes the old session and issues a new pair in a single transaction

`POST /api/auth/refresh` MUST accept the current refresh token in the `Authorization: Bearer` header. The service MUST compute the Argon2id hash of the presented token, look up the `auth_session` by hash, and:

- If no row is found → respond `401` with `code = "AUTH_TOKEN_REVOKED"`.
- If the row exists and `revoked_at IS NOT NULL` → **reuse detected**: walk the chain via `rotated_to_id`/`replaced_by_id` from this row forward, set `revoked_at = now()` on every row in the chain that does not already have one, emit `AUTH_REFRESH_REUSE_DETECTED`, respond `401` with `code = "AUTH_TOKEN_REVOKED"`.
- If the row exists, `revoked_at IS NULL`, and `expires_at < now()` → respond `401` with `code = "AUTH_TOKEN_EXPIRED"`.
- Otherwise, in a single database transaction: set the current row's `revoked_at = now()` and `last_used_at = now()`, create a new `auth_session` row with a new `jti`, a new `refresh_token_hash` (Argon2id of the new refresh token), a new `expires_at`, set `rotated_to_id` on the old row to the new row's id, and set `replaced_by_id` on the new row to the old row's id. Mint a new access token and a new refresh token. Emit `AUTH_REFRESH_ROTATE` with the old and new session ids. Return the new pair.

The refresh token rotation SHALL generate a completely new JWT on each rotation (new `jti`, new UUID), store the new token's hash in a new `auth_session` row, and link old and new sessions via `rotated_to_id` / `replaced_by_id`.

#### Scenario: A valid refresh token rotates to a new session with a new jti

- **WHEN** `POST /api/auth/refresh` is called with a valid, non-revoked refresh token
- **THEN** a new `auth_session` row is created with a new `jti`, new `refresh_token_hash`, new UUID, and `expires_at = now() + REFRESH_TOKEN_EXPIRE_MINUTES`
- **AND** the old session row has `revoked_at = now()`
- **AND** `old_session.rotated_to_id` points to the new session's id
- **AND** `new_session.replaced_by_id` points to the old session's id
- **AND** the response contains a NEW refresh token (different from the previous one)

#### Scenario: Reusing a rotated token triggers chain-wide revocation

- **WHEN** `POST /api/auth/refresh` is called with a refresh token whose session row has `revoked_at IS NOT NULL`
- **THEN** every session in the rotation chain (follow `rotated_to_id` forward) has `revoked_at = now()` set
- **AND** the response is `401` with `code = "AUTH_TOKEN_REVOKED"`
- **AND** an audit event with action `AUTH_REFRESH_REUSE_DETECTED` is emitted

#### Scenario: An expired refresh token returns 401 AUTH_TOKEN_EXPIRED

- **WHEN** a `POST /api/auth/refresh` is sent with a refresh token whose session row has `expires_at < now()` and `revoked_at IS NULL`
- **THEN** the response is `401` with `code = "AUTH_TOKEN_EXPIRED"`
- **AND** no rotation is performed
- **AND** no new session row is created

#### Scenario: A token whose signature does not verify is rejected

- **WHEN** a `POST /api/auth/refresh` is sent with a token that does not verify against `Settings.SECRET_KEY`
- **THEN** the response is `401` with `code = "AUTH_TOKEN_REVOKED"` (signature mismatch is treated as revoked for parity with the rest of the surface)

### Requirement: The system revokes the active session on logout

`POST /api/auth/logout` MUST accept the current refresh token in the `Authorization: Bearer` header. The service MUST look up the `auth_session` by hash, set `revoked_at = now()` if not already set, emit `AUTH_LOGOUT`, and respond `204 No Content`. Calling logout with an already-revoked token MUST also respond `204` (idempotent) and MUST NOT emit a second `AUTH_LOGOUT` audit event.

#### Scenario: Logout revokes the session and returns 204

- **WHEN** a `POST /api/auth/logout` is sent with a valid refresh token whose session is active
- **THEN** the response is `204` with no body
- **AND** the session row has `revoked_at` set to the current time
- **AND** an audit event with action `AUTH_LOGOUT` is emitted

#### Scenario: Logout on an already-revoked session is a no-op and still returns 204

- **WHEN** a `POST /api/auth/logout` is sent with a refresh token whose session already has `revoked_at IS NOT NULL`
- **THEN** the response is `204` with no body
- **AND** `revoked_at` is not changed
- **AND** no new `AUTH_LOGOUT` audit event is emitted

### Requirement: The system provides password recovery with a single-use, hashed token

`POST /api/auth/forgot` MUST accept `{tenant_codigo, email}`. The service MUST resolve the tenant by `codigo`. If the tenant is missing, soft-deleted, or inactive → respond `200` with the same body the success case returns, after a constant-time delay of ~200ms, and emit no audit event. If the user is missing, soft-deleted, or `is_active = false` → respond `200` with the same body after the same delay, and emit no audit event. Otherwise: generate a 32-byte URL-safe random token, store `{selector, token_hash = argon2id(token), user_id, tenant_id, expires_at = now() + PASSWORD_RESET_TOKEN_TTL_MINUTES, used_at = NULL}` in `auth_password_reset`, dispatch the email through the `integrations/email` seam, emit `AUTH_PASSWORD_RESET_REQUEST` with the `reset_id` (not the token), and respond `200` with `{status: "ok"}` after the same delay.

`POST /api/auth/reset` MUST accept `{tenant_codigo, token, new_password}`. The service MUST resolve the tenant, look up the `auth_password_reset` row by `selector` (the first 8 chars of the token id stored separately — implementation detail, but the lookup MUST be O(1) on the index), Argon2id-verify the token against `token_hash`, and:

- If no row is found or the token does not verify → respond `401` with `code = "AUTH_RESET_INVALID"`.
- If the row is found, the token verifies, but `expires_at < now()` → respond `401` with `code = "AUTH_RESET_EXPIRED"`.
- If the row is found, the token verifies, and `used_at IS NOT NULL` → respond `401` with `code = "AUTH_RESET_INVALID"` (replay protection).
- Otherwise: set the user's new Argon2id-hashed password, set `used_at = now()`, revoke every active `auth_session` row for that user (set `revoked_at = now()`), emit `AUTH_PASSWORD_RESET_OK`, and respond `200` with `{status: "ok"}`.

The new password MUST satisfy `Settings.PASSWORD_MIN_LENGTH` (default 12) and MUST NOT be the same as the previous password (a server-side reject, not a warning).

#### Scenario: Forgot-password for a known user stores a hashed token and dispatches the email

- **WHEN** a `POST /api/auth/forgot` is sent with a known `tenant_codigo` and a known email
- **THEN** the response is `200` with `{status: "ok"}` after a delay of at least 200ms
- **AND** a row exists in `auth_password_reset` with `token_hash` equal to the Argon2id hash of a 32-byte URL-safe random token, `used_at IS NULL`, and `expires_at = created_at + PASSWORD_RESET_TOKEN_TTL_MINUTES`
- **AND** the test email collector has received a message whose body contains the plaintext token (because the test seam does not encrypt outbound mail; the production seam must not log the token)
- **AND** an audit event with action `AUTH_PASSWORD_RESET_REQUEST` is emitted with the `reset_id` (UUID), not the token

#### Scenario: Forgot-password for an unknown user returns the same 200 after the same delay

- **WHEN** a `POST /api/auth/forgot` is sent with a known `tenant_codigo` and an unknown email
- **THEN** the response is `200` with `{status: "ok"}` after a delay within `±50ms` of the known-user case
- **AND** no `auth_password_reset` row is created
- **AND** no email is dispatched
- **AND** no audit event is emitted

#### Scenario: Reset-password with a valid unused token rotates the password and revokes sessions

- **WHEN** a `POST /api/auth/reset` is sent with a valid `token`, the matching `auth_password_reset` row exists, `expires_at > now()`, and `used_at IS NULL`
- **THEN** the response is `200` with `{status: "ok"}`
- **AND** the user's `auth_user.password_hash` is the Argon2id hash of the new password
- **AND** the `auth_password_reset.used_at` is set to the current time
- **AND** every `auth_session` row for the user has `revoked_at` set to the current time
- **AND** an audit event with action `AUTH_PASSWORD_RESET_OK` is emitted

#### Scenario: Reset-password with an already-used token returns 401 AUTH_RESET_INVALID

- **WHEN** a `POST /api/auth/reset` is sent with a token whose `auth_password_reset.used_at IS NOT NULL`
- **THEN** the response is `401` with `code = "AUTH_RESET_INVALID"`
- **AND** the user's password is not changed
- **AND** no `auth_password_reset` row is mutated

#### Scenario: Reset-password with an expired token returns 401 AUTH_RESET_EXPIRED

- **WHEN** a `POST /api/auth/reset` is sent with a valid token whose `auth_password_reset.expires_at < now()` and `used_at IS NULL`
- **THEN** the response is `401` with `code = "AUTH_RESET_EXPIRED"`
- **AND** the user's password is not changed

#### Scenario: Reset-password rejects a password equal to the current one

- **WHEN** a `POST /api/auth/reset` is sent with a valid token and a `new_password` that is byte-equal to the current password (after normalization)
- **THEN** the response is `400` with a validation error indicating the password must differ from the current one
- **AND** the password is not changed
- **AND** the `auth_password_reset.used_at` is not set (the token is still valid; the user can retry with a different password)

### Requirement: Users can enroll and verify TOTP second factor

`POST /api/auth/2fa/enroll` MUST require an authenticated session (a valid access token). The service MUST generate a 32-character base32 secret, store the secret encrypted in `auth_user.totp_secret_enc` (AAD `auth_user.totp_secret`, AES-256-GCM), leave `totp_enabled = false`, and respond `200` with `{otpauth_uri, secret, qr_png_base64?}` (the QR PNG is optional, controlled by a setting; the URI and the secret are always returned). The endpoint MUST be idempotent in the sense that re-enrollment overwrites the encrypted secret and resets `totp_enabled = false`; the user must verify a code before 2FA is active.

`POST /api/auth/2fa/verify` MUST require an authenticated session. The service MUST decrypt `auth_user.totp_secret_enc`, run `pyotp.TOTP(secret).verify(code, valid_window=1)`, and:

- If no `auth_user.totp_secret_enc` is set (the user has not called `enroll`) → respond `400` with a validation error.
- If the code verifies and `totp_enabled = false` → set `totp_enabled = true`, emit `AUTH_2FA_ENROLL`.
- If the code verifies and `totp_enabled = true` → respond `200` with `{totp_enabled: true}` (re-verify is a status check, no new audit).
- If the code does not verify → respond `401` with `code = "AUTH_2FA_INVALID"`, do not change `totp_enabled`, emit `AUTH_2FA_VERIFY_FAIL`.

The `secret` field is returned **only** by `enroll`, never by `verify`.

#### Scenario: Enroll returns an otpauth URI and the secret, and totp_enabled is false until verify

- **WHEN** an authenticated user calls `POST /api/auth/2fa/enroll`
- **THEN** the response is `200` with a JSON body containing `otpauth_uri` (an `otpauth://totp/...` URI), `secret` (the 32-char base32 string), and optionally `qr_png_base64`
- **AND** the `auth_user.totp_secret_enc` column holds the AES-256-GCM ciphertext of the secret (AAD `auth_user.totp_secret`)
- **AND** `auth_user.totp_enabled` is `false`

#### Scenario: Verify with a valid code sets totp_enabled to true

- **WHEN** an authenticated user who has just called `enroll` calls `POST /api/auth/2fa/verify` with a 6-digit code matching the encrypted secret
- **THEN** the response is `200` with `{totp_enabled: true}`
- **AND** `auth_user.totp_enabled` is `true`
- **AND** an audit event with action `AUTH_2FA_ENROLL` is emitted

#### Scenario: Verify with an invalid code does not enable 2FA

- **WHEN** an authenticated user calls `POST /api/auth/2fa/verify` with a code that does not match the secret
- **THEN** the response is `401` with `code = "AUTH_2FA_INVALID"`
- **AND** `auth_user.totp_enabled` is not changed
- **AND** an audit event with action `AUTH_2FA_VERIFY_FAIL` is emitted

#### Scenario: Verify without a prior enroll returns 400

- **WHEN** an authenticated user calls `POST /api/auth/2fa/verify` and `auth_user.totp_secret_enc IS NULL`
- **THEN** the response is `400` with a validation error indicating enrollment is required

### Requirement: The dependency `get_current_user` resolves identity and tenant from the verified JWT and sets the per-task tenant context

The system MUST provide a FastAPI dependency `get_current_user` that:

1. Reads `Authorization: Bearer <token>` from the request. If absent or malformed → respond `401` with `code = "AUTH_TOKEN_MISSING"`.
2. Decodes the token using `core/security/jwt.py:decode_access_token`. The decoder MUST verify the signature with `Settings.SECRET_KEY`, MUST verify `typ == "access"`, MUST verify `exp` is in the future, MUST verify `iat` is in the past (with a small clock skew tolerance, default 30s). On any failure → respond `401` with the appropriate code (`AUTH_TOKEN_EXPIRED`, `AUTH_TOKEN_REVOKED`, etc.).
3. Loads the `auth_user` row by `sub`. If missing, soft-deleted, or `is_active = false` → respond `401` with `code = "AUTH_TOKEN_REVOKED"`.
4. Loads the `auth_session` row by `sid`. If missing or `revoked_at IS NOT NULL` → respond `401` with `code = "AUTH_TOKEN_REVOKED"`.
5. Asserts `auth_user.tenant_id == auth_session.tenant_id`. If they differ → respond `401` with `code = "AUTH_TOKEN_REVOKED"`.
6. Constructs a `CurrentUser` value object with `user_id`, `tenant_id`, `session_id`, `is_2fa_verified` (true if the session was opened via a 2FA-verified login OR if the user has no 2FA enabled at all).
7. Sets a `TenantContext(tenant_id, is_impersonating=False)` on the per-task `ContextVar`.
8. Returns the `CurrentUser`.

The system MUST also provide `get_optional_current_user`, which does the same but returns `None` instead of raising on missing or invalid tokens. This dependency is for endpoints that accept anonymous traffic (none in C-03, but the contract is part of the spec for C-21 to consume).

#### Scenario: get_current_user resolves the user from a valid access token and sets the tenant context

- **WHEN** a request to an authenticated endpoint carries `Authorization: Bearer <valid access token>` whose `sub` is a known user and whose `tid` and `sid` match an active session
- **THEN** the dependency returns a `CurrentUser` whose `user_id` equals the user's UUID, `tenant_id` equals the user's tenant, `session_id` equals the session's UUID
- **AND** `get_current_tenant_id()` returns the same `tenant_id`
- **AND** the request proceeds to the handler

#### Scenario: get_current_user rejects a request with a missing Authorization header

- **WHEN** a request to an authenticated endpoint has no `Authorization` header
- **THEN** the dependency raises `401` with `code = "AUTH_TOKEN_MISSING"`
- **AND** no `TenantContext` is set

#### Scenario: get_current_user rejects a request with a malformed token

- **WHEN** a request to an authenticated endpoint has `Authorization: Bearer garbage`
- **THEN** the dependency raises `401` with `code = "AUTH_TOKEN_REVOKED"` (signature failure is treated as revoked for parity)

#### Scenario: get_current_user rejects an expired access token

- **WHEN** a request to an authenticated endpoint has a valid signature but `exp` is in the past
- **THEN** the dependency raises `401` with `code = "AUTH_TOKEN_EXPIRED"`

#### Scenario: get_current_user rejects a refresh token presented as an access token

- **WHEN** a request to an authenticated endpoint has a token whose `typ` is `"refresh"`
- **THEN** the dependency raises `401` with `code = "AUTH_TOKEN_REVOKED"`

#### Scenario: get_current_user rejects a session that has been revoked

- **WHEN** a request to an authenticated endpoint has a valid access token whose `sid` points to a session with `revoked_at IS NOT NULL`
- **THEN** the dependency raises `401` with `code = "AUTH_TOKEN_REVOKED"`

#### Scenario: get_current_user ignores any request-supplied identity

- **WHEN** a request to an authenticated endpoint carries a valid access token **and** also includes `?as_user_id=<UUID>`, `?as_tenant_id=<UUID>`, an `X-Impersonate-User` header, an `X-Tenant-Id` header, a body field `user_id`, or a path parameter `user_id`
- **THEN** the dependency returns the `CurrentUser` derived from the verified JWT
- **AND** the `user_id`, `tenant_id`, and `session_id` of the `CurrentUser` are the values from the JWT, never from any of the request-supplied fields
- **AND** the test `tests/auth/test_identity_immutability.py` enumerates these surfaces and asserts the result

#### Scenario: get_optional_current_user returns None for an anonymous request

- **WHEN** a request to an endpoint that uses `get_optional_current_user` has no `Authorization` header
- **THEN** the dependency returns `None`
- **AND** no `TenantContext` is set
- **AND** no `401` is raised

### Requirement: The tenant context dependency no longer reads the X-Tenant-Id header

The `tenant_context_dep` in `app/core/dependencies.py` MUST resolve the tenant from the verified JWT via `get_current_user`, not from an `X-Tenant-Id` header. Reading the header MUST raise at startup or in tests as a `NotImplementedError`-equivalent seam, and the FastAPI application MUST NOT register a route that reads it. The placeholder body present in C-02 (`x_tenant_id: UUID | None = Header(default=None, alias="X-Tenant-Id")`) MUST be removed.

The contract of the dependency — it returns a `TenantContext` and sets it on the per-task `ContextVar` — MUST NOT change. Services that call `get_current_tenant_id()` keep working.

#### Scenario: A request with a valid JWT resolves the tenant from the token, not the header

- **WHEN** a request carries a valid access JWT with `tid = T1` **and** an `X-Tenant-Id: T2` header
- **THEN** `get_current_tenant_id()` returns `T1` and the repository is bound to `T1`
- **AND** the `X-Tenant-Id` header is ignored

#### Scenario: The C-02 X-Tenant-Id placeholder is gone

- **WHEN** the application starts and the OpenAPI schema is generated
- **THEN** no endpoint declares an `X-Tenant-Id` header parameter
- **AND** a search of `backend/app/` for `X-Tenant-Id` returns no matches outside the archived C-02 migration notes

#### Scenario: C-02 tests that used the header are migrated

- **WHEN** the C-02 test suite is run after the C-03 change
- **THEN** every test that previously sent `X-Tenant-Id` either (a) mints a JWT for a known user and uses the HTTP client, or (b) sets the tenant context directly via `set_tenant_context(TenantContext(tenant_id=...))` in a fixture
- **AND** no test sends an `X-Tenant-Id` header

### Requirement: The auth subsystem emits audit events through the C-02 seam with documented action codes

The auth services MUST emit audit events through `core/audit.py:audit_emit` (the C-02 seam) using the following action codes:

- `AUTH_LOGIN_OK` — successful login (any flow).
- `AUTH_LOGIN_FAIL` — wrong password, wrong 2FA code, or 2FA required but missing.
- `AUTH_REFRESH_ROTATE` — successful refresh-token rotation.
- `AUTH_REFRESH_REUSE_DETECTED` — a refresh token that was already rotated was presented again.
- `AUTH_LOGOUT` — successful logout.
- `AUTH_PASSWORD_RESET_REQUEST` — `forgot` for a known user.
- `AUTH_PASSWORD_RESET_OK` — successful password reset.
- `AUTH_2FA_ENROLL` — 2FA successfully enrolled (first verify of a new secret).
- `AUTH_2FA_VERIFY_FAIL` — 2FA verify with an invalid code.

Every emitted audit event MUST include `tenant_id` and either `user_id` (when known) or `email_hash` (when the user is unknown — only for `AUTH_LOGIN_FAIL`). No audit event MUST include plaintext email, plaintext password, plaintext TOTP code, plaintext refresh token, or the recovery token.

#### Scenario: AUTH_LOGIN_OK is emitted with user_id and tenant_id

- **WHEN** a successful login completes
- **THEN** the audit payload contains `action = "AUTH_LOGIN_OK"`, `user_id` (the user's UUID), and `tenant_id` (the tenant's UUID)
- **AND** no plaintext email, password, TOTP code, or token is present

#### Scenario: AUTH_LOGIN_FAIL with unknown user emits email_hash but not plaintext

- **WHEN** a login attempt fails for an unknown user (or for a known user with a wrong password)
- **THEN** the audit payload contains `action = "AUTH_LOGIN_FAIL"`, `email_hash` (SHA-256 of the lowercased email), `tenant_id_hash` (or `tenant_id` if the tenant existed), and `reason` (one of `WRONG_PASSWORD`, `WRONG_TOTP`, `MISSING_TOTP`, `UNKNOWN_USER`, `INACTIVE_USER`)
- **AND** no plaintext email, password, TOTP code, or token is present

#### Scenario: AUTH_REFRESH_REUSE_DETECTED includes the originating session id

- **WHEN** a previously rotated refresh token is presented
- **THEN** the audit payload contains `action = "AUTH_REFRESH_REUSE_DETECTED"` and `session_id` (the id of the row that was already revoked)
- **AND** no plaintext refresh token is present

### Requirement: Auth PII is encrypted with the C-02 AES-256 helper and never logged

The fields `auth_user.email_enc` and `auth_user.totp_secret_enc` MUST be encrypted with the C-02 `core/security/crypto.py` helper. The AAD for the email column MUST be `"auth_user.email"`, and the AAD for the TOTP column MUST be `"auth_user.totp_secret"`. Decryption of these columns MUST use the same AAD; a row encrypted for one tenant MUST NOT decrypt under another tenant (the C-02 helper guarantees this).

The auth services MUST NOT log the plaintext email, the plaintext TOTP secret, the plaintext password, the plaintext refresh token, the plaintext access token, or the plaintext recovery token. Logger calls in the auth subsystem MUST pass these values only as opaque identifiers (`user_id`, `session_id`, `reset_id`, `email_hash`, `token_id_prefix`).

#### Scenario: auth_user.email_enc is round-trip encrypted under the right AAD

- **WHEN** the auth service stores a new `auth_user` row with `email = "alice@example.com"` in tenant `T1`
- **THEN** `auth_user.email_enc` is the base64 envelope produced by `core.security.crypto.encrypt(plaintext, tenant_id=T1, aad_suffix="auth_user.email")`
- **AND** `core.security.crypto.decrypt(auth_user.email_enc, tenant_id=T1, aad_suffix="auth_user.email")` returns `"alice@example.com"`

#### Scenario: A row encrypted in tenant T1 does not decrypt under tenant T2

- **WHEN** an `auth_user` row is encrypted in tenant `T1`
- **AND** an attempt is made to decrypt the `email_enc` under tenant `T2` with the same AAD
- **THEN** the helper raises `CryptoError` and no plaintext is returned

#### Scenario: The auth subsystem never logs plaintext credentials

- **WHEN** any auth code path is exercised (login, refresh, logout, forgot, reset, 2FA enroll, 2FA verify)
- **THEN** no log record contains the plaintext email, password, TOTP code, refresh token, access token, or recovery token
- **AND** the test `tests/auth/test_no_plaintext_in_logs.py` captures all log records during a representative end-to-end flow and asserts the absence
