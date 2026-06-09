## Why

activia-trace needs a real authentication layer on top of the multi-tenant foundations of C-02. Today the placeholder `tenant_context_dep` reads the `X-Tenant-Id` header, so there is no real session, no way to log in, and no way for a request to know who the user is. C-03 closes that gap with a self-contained auth subsystem (ADR-001): email + password (Argon2id), JWT access 15 min + refresh rotation, optional TOTP 2FA, password recovery, and a `get_current_user` dependency that becomes the only source of identity and tenant for every subsequent change. C-03 sits on the critical path: C-04 (RBAC), C-21 (frontend auth), and every later backend change depend on `get_current_user` existing and being trustworthy.

## What Changes

- **`POST /api/auth/login`** — accept `{tenant_codigo, email, password, totp_code?}`; verify password (Argon2id); if user has TOTP enrolled, require a valid `totp_code` in the same call; emit `{access_token, refresh_token, token_type, expires_in, requires_2fa?}`; record `LOGIN_OK` / `LOGIN_FAIL` through the `audit_emit` seam.
- **`POST /api/auth/refresh`** — accept the current refresh token; rotate it (mark the old one revoked, issue a new pair) inside a single transaction; emit `REFRESH_ROTATE`; reject reuse of a previously-rotated token (the entire chain is invalidated).
- **`POST /api/auth/logout`** — revoke the presented refresh token (`session_id` row is soft-deleted with `revoked_at = now()`); emit `LOGOUT`. Idempotent on already-revoked tokens.
- **`POST /api/auth/forgot`** — accept `{tenant_codigo, email}`; if a user exists, generate a single-use recovery token (Argon2id-hashed at rest), store it with a short TTL (`PASSWORD_RESET_TOKEN_TTL_MINUTES`, default 30), and dispatch the email through the existing `integrations/email` seam. Constant-time response regardless of whether the email exists.
- **`POST /api/auth/reset`** — accept `{token, new_password}`; look up the hashed token; on match, set the new password, mark the token used, and revoke all active refresh tokens for that user. Emit `PASSWORD_RESET_OK`.
- **`POST /api/auth/2fa/enroll`** (authenticated) — generate a TOTP secret, return an `otpauth://` URI + QR payload; the user must verify a code in the next call before 2FA is active.
- **`POST /api/auth/2fa/verify`** (authenticated) — accept a 6-digit code; on first valid code, set `totp_enabled = true` and store the secret encrypted (AES-256, AAD `auth_user.totp_secret`); subsequent calls return the current TOTP status. Used both for enrollment confirmation and for 2FA-gated login.
- **Dependency `get_current_user`** — extract and verify the bearer JWT (signature, `exp`, `iat`, `jti`), resolve the `auth_user` row, build a `CurrentUser` value object (user_id, tenant_id, session_id, is_2fa_verified) and a `TenantContext`, and set the per-task `ContextVar`. The dependency is the **only** path through which downstream services resolve identity or tenant.
- **Dependency `get_optional_current_user`** — same as above but returns `None` instead of raising 401. Used by endpoints that accept anonymous traffic (none in C-03, but the contract is part of the spec for C-21 to consume).
- **In-memory rate limiter** — `5 / 60s` per `(client_ip, email_lower)` on the login endpoint, with a sliding window. Documented as in-memory (no Redis); a future change may swap the backend.
- **Replacement of the C-02 `tenant_context_dep` placeholder** — the resolver is now JWT-driven; the legacy `X-Tenant-Id` header path is removed entirely. Existing tests in C-02 that use the header are migrated to call `set_tenant_context` directly in fixtures (the seam is unchanged).
- **Config additions** in `core/config.py` (no breaking renames): `REFRESH_TOKEN_EXPIRE_MINUTES` (default `60 * 24 * 7`), `PASSWORD_RESET_TOKEN_TTL_MINUTES` (default `30`), `LOGIN_RATE_LIMIT_PER_MINUTE` (default `5`), `LOGIN_RATE_LIMIT_WINDOW_SECONDS` (default `60`), `TOTP_ISSUER` (default `"activia-trace"`), `PASSWORD_MIN_LENGTH` (default `12`).

**BREAKING**: the C-02 `tenant_context_dep` shape is kept (still returns a `TenantContext`), but the input is now the verified JWT instead of the `X-Tenant-Id` header. C-02 tests that relied on the header must be updated to use the `tenant_scope` context manager or a fixture that sets the context directly.

## Capabilities

### New Capabilities

- `auth-jwt-2fa`: end-to-end authentication subsystem — login with credentials, TOTP-gated session issuance, refresh-token rotation, password recovery, and the `get_current_user` dependency that downstream changes consume.
- `auth-rate-limit`: a thin, swappable in-memory sliding-window limiter keyed on `(ip, subject)` with a 60-second default window; bound to the login endpoint in C-03 and exposed as a utility for later endpoints.

### Modified Capabilities

- `tenancy-foundation`: the `tenant_context_dep` placeholder that read `X-Tenant-Id` is replaced by a JWT-driven resolver. The `TenantContext` shape and the `get_current_tenant_id()` contract do **not** change — services downstream keep working. The capability's "## ADDED Requirements" stay; C-03 adds a delta requirement covering the resolver swap.
- `app-configuration`: `core/config.py` gains the new settings above. The capability is touched in implementation, not in requirement semantics (no new behavior is specified, only new fields are added with their defaults), so no spec-level requirement is added.

## Impact

**Code**:
- New modules under `backend/app/auth/` (routers, services, repositories, schemas, models, dependencies, security helpers).
- `backend/app/core/dependencies.py` — replace the `tenant_context_dep` body with the JWT resolver; add `get_current_user`, `get_optional_current_user`. The `X-Tenant-Id` header path is deleted.
- `backend/app/core/config.py` — add the five new settings.
- `backend/app/core/security/` — add `jwt.py` (encode/decode/verify) and `passwords.py` (Argon2id wrapper).
- `backend/app/models/` — new `auth_user.py` and `auth_session.py` and `auth_password_reset.py` ORM models, all using `TenantScopedMixin`.
- `backend/app/repositories/` — new `auth_user_repo.py`, `auth_session_repo.py`, `auth_password_reset_repo.py`, all extending `TenantScopedRepository`.
- `backend/app/services/` — new `auth_service.py`, `password_reset_service.py`, `two_factor_service.py`, `rate_limit_service.py`.
- `backend/app/api/v1/routers/` — new `auth.py`, `two_factor.py`, `password_reset.py`. Mounted under `/api/auth/*`.
- `backend/alembic/versions/` — one migration: `002_auth_user_auth_session_auth_password_reset.py`.
- `backend/tests/` — new test modules under `tests/auth/`, `tests/core/` (for the new `get_current_user` and rate limiter), and updated fixtures in `tests/conftest.py` (header → JWT, or fixture-only context).

**APIs**:
- New public endpoints under `/api/auth/*` (login, refresh, logout, forgot, reset, 2fa/enroll, 2fa/verify).
- The error envelope reuses the C-02 convention (Pydantic-validated 4xx with a stable `code` field); new error codes: `AUTH_INVALID_CREDENTIALS`, `AUTH_2FA_REQUIRED`, `AUTH_2FA_INVALID`, `AUTH_RATE_LIMITED`, `AUTH_TOKEN_EXPIRED`, `AUTH_TOKEN_REVOKED`, `AUTH_RESET_INVALID`, `AUTH_RESET_EXPIRED`.
- OpenAPI tags: `Auth`, `TwoFactor`, `PasswordReset`.

**Dependencies** (added to `pyproject.toml`):
- `pyotp` (TOTP, RFC 6238).
- `qrcode[pil]` (server-side QR PNG for the 2FA enrollment response — optional, controlled by a flag).
- `argon2-cffi` (already in C-01; version pin confirmed).
- `python-jose[cryptography]` (already in C-01 for JWT; version pin confirmed).
- `httpx` (already in C-01; reused for the email-seam integration test).

**Systems**:
- The audit emission uses the C-02 `audit_emit` seam — C-05 will wire it to the persistent `AuditLog` table. C-03 introduces new action codes (`AUTH_LOGIN_OK`, `AUTH_LOGIN_FAIL`, `AUTH_REFRESH_ROTATE`, `AUTH_LOGOUT`, `AUTH_PASSWORD_RESET_REQUEST`, `AUTH_PASSWORD_RESET_OK`, `AUTH_2FA_ENROLL`, `AUTH_2FA_VERIFY`) which the seam currently warns about as "unknown codes" — that is acceptable and reviewed: the seam's vocabulary is extended by C-03, not by C-05.
- The `integrations/email` seam is **not** yet implemented (it lives in a later change). C-03 defines the seam and the recovery flow; the email delivery is stubbed in the test suite with an in-memory collector and emits a `INFO` log line with the masked recipient and a token URL that the test can read. The seam is the only place that needs to change when a real email provider lands.
- No frontend work in C-03 (C-21 owns the login UI). C-03 exposes the contract that C-21 will consume.

**Out of scope (deferred to other changes)**:
- Real email delivery (`integrations/email`).
- Redis-backed rate limiting.
- Account lockout (out of scope for MVP; rate limit is the brute-force defense).
- Email enumeration hardening beyond constant-time responses on `/forgot`.
- Impersonation (C-05).
- Roles / permissions (C-04).
- `Usuario` model with full PII (C-07) — see design.md D0 for the migration path.
