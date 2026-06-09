## Context

C-01 (foundation) and C-02 (core-models-y-tenancy) are merged on `main`. The system has a working FastAPI skeleton, PostgreSQL with Alembic, multi-tenant scaffolding (the `tenant` table, `TenantScopedMixin`, `TenantScopedRepository[T]`, `tenant_scope` ContextVar), AES-256-GCM PII encryption, and a placeholder `tenant_context_dep` that reads the `X-Tenant-Id` header for tests and the smoke endpoint.

The placeholder is a debt: there is no real auth, no users, no sessions, no roles. C-04 (RBAC) cannot start without a working `get_current_user`. C-21 (frontend shell + auth) cannot start without `/api/auth/*` endpoints. C-07 (usuarios-y-asignaciones) introduces the full `Usuario` model with PII cifrada and `Asignacion` with vigencia, but `get_current_user` must exist **before** C-07 ships — otherwise there is no way to resolve the user calling the user-management endpoints.

C-03 closes that gap with a self-contained auth subsystem that ADR-001 calls for: email + password (Argon2id), JWT access 15 min + refresh with rotation, optional TOTP 2FA, password recovery, rate limiting, and a `get_current_user` dependency that becomes the only source of identity and tenant for everything downstream.

The change touches the **security core** of the product. A single bug here is a multi-tenant data breach. Governance is **CRÍTICO** — analysis and proposal only; the design and tasks below are reviewed and approved before any code is written.

## Goals / Non-Goals

**Goals:**

- Provide a working `/api/auth/*` surface that can be called from a real client (C-21).
- Make `get_current_user` the only way any request obtains its identity and tenant.
- Honor the C-02 contracts: `TenantContext`, `get_current_tenant_id()`, `TenantScopedRepository`, `audit_emit` seam, AES-256 helper — none of which C-03 may break.
- Strict TDD: every endpoint, helper, and edge case (rotation, 2FA, recovery, rate limit, identity immutability) has at least one failing test before the production code that satisfies it.
- Cover ≥80% of lines and ≥90% of the new business rules with tests that use a real PostgreSQL test database (no mocked DB).
- One Alembic migration that introduces `auth_user`, `auth_session`, and `auth_password_reset`.
- Migration path to C-07 explicitly documented (D0).

**Non-Goals:**

- Roles, permissions, or the `Usuario` PII model (C-04, C-07).
- AuditLog persistence (C-05); C-03 uses the C-02 seam.
- Real email delivery; C-03 stubs the seam and provides a test collector.
- Account lockout; rate limit is the brute-force defense.
- Multi-factor beyond TOTP (no SMS, no WebAuthn in MVP).
- Impersonation (C-05).
- Refresh-token rotation detection chains beyond a single reuse (C-03 invalidates the whole chain on reuse; C-05+ can refine if needed).

## Decisions

### D0 — User model: minimal `auth_user` in C-03, extended by C-07

**Tension.** C-07 will introduce the full `Usuario` model with PII cifrada (`email`, `dni`, `cuil`, `cbu`, `alias_cbu`), `legajo` as a business attribute, and `Asignacion` with vigencia. C-03 needs users to authenticate, but cannot create a model that C-07 will have to break. The CHANGES.md C-07 scope already states `Migración 005: usuario, asignacion` — so C-07 will own a new migration.

**Options considered.**

1. **Minimal `auth_user` in C-03** — the model carries only what auth needs: `id`, `tenant_id`, `email` (PII cifrada with AAD `auth_user.email`), `password_hash` (Argon2id), `totp_secret_enc` (nullable, AES-256-GCM, AAD `auth_user.totp_secret`), `totp_enabled` (bool, default `false`), `is_active` (bool, default `true`), `failed_login_count`, `last_login_at`, plus the standard `TenantScopedMixin` columns. C-07 introduces a new `usuario` model (PII complete) and decides the consolidation: either (a) add columns to `auth_user` (rename to `auth_user` → `usuario` and migrate), or (b) keep `auth_user` as the credential slice and reference it from `usuario` (a 1:1 by `user_id`). **Recommended.**
2. **No model in C-03, stub the user in tests.** Rejected: C-04 needs a real `get_current_user` that resolves roles, which means a real `auth_user` row whose `id` is referenced from `auth_session`. A stub cannot survive past C-04.
3. **C-03 owns the full `Usuario` model.** Rejected: it would pull PII encryption design, legajo semantics, and `Asignacion` into a change that is supposed to be scoped to authentication. C-07 already has those decisions in its scope.

**Recommendation: option 1.** The migration path to C-07 is documented in `Migration Plan` below.

**Email uniqueness: per-tenant.** `UNIQUE (tenant_id, email_enc)`. The same email may exist in two different institutions, which is realistic and consistent with ADR-002 (row-level, one DB, `tenant_id` scopes everything). The lookup on login is `(tenant_codigo → tenant_id, email)`. A global unique index would be the wrong call.

### D1 — JWT claims and role resolution

**Claims (access token).** Minimum:

| Claim | Source | Purpose |
|-------|--------|---------|
| `sub` | `auth_user.id` | Who is the user. |
| `tid` | `auth_user.tenant_id` | Which tenant. Verified against the request URL on every request. |
| `sid` | `auth_session.id` | The session row; refresh rotation walks back to it. |
| `iat` | server clock | Issued at. |
| `exp` | `iat + ACCESS_TOKEN_EXPIRE_MINUTES` | Expiry. |
| `jti` | `uuid4()` | Per-token unique id. |
| `typ` | `"access"` | Distinguishes from refresh tokens. |

**Roles are NOT in the token.** The C-02 spec already establishes that roles are resolved server-side per request from a cache. Putting roles in the token would force re-login on every role change, which is hostile to the COORDINADOR who toggles roles frequently during setup. C-04 will own the cache; C-03 stores only `sub`, `tid`, `sid` and leaves the rest to a follow-up resolver wired in C-04.

**Tenant claim must match the resolved tenant.** When the `auth_user` row is loaded, the service asserts `auth_user.tenant_id == tenant_context.tenant_id`; mismatch is a 401 (the token is structurally valid but the user no longer belongs to the tenant the token was issued for — rare, but possible after a tenant migration).

### D2 — Refresh token storage and rotation

**DB-backed, with `jti` and a token hash.** The `auth_session` row stores:

- `id` (UUID)
- `user_id`, `tenant_id` (denormalized for fast lookups, kept in sync via FK ON DELETE CASCADE)
- `refresh_token_hash` (Argon2id of the opaque token string; never store the raw token)
- `jti` (UUID, unique index, used for O(1) lookups)
- `issued_at`, `expires_at`, `last_used_at`
- `revoked_at` (nullable; soft delete)
- `rotated_to_id` (nullable FK to the next session row; gives a chain pointer)
- `ip_origen`, `user_agent` (for the audit; the IP is the one the request was made from, never trusted as identity)
- `replaced_by_id` (the previous session that this one rotated from; closure of the chain)

**Rotation flow.**

1. Client calls `POST /api/auth/refresh` with the refresh token.
2. Server reads the bearer, computes its Argon2id hash, finds `auth_session` by hash.
3. If `revoked_at IS NOT NULL` → reuse detected: **invalidate the entire chain** (set `revoked_at = now()` on every session in the chain via `rotated_to_id` walk), emit `AUTH_REFRESH_REUSE_DETECTED`, return 401.
4. If `expires_at < now()` → expired: 401.
5. Else: in a single transaction, mark this session `revoked_at = now()`, create a new `auth_session` with a new `jti` and a new `refresh_token_hash`, set `rotated_to_id = new.id` and `replaced_by_id = old.id`. Issue a new access token and a new refresh token. Emit `AUTH_REFRESH_ROTATE`.

The chain walk is bounded by `REFRESH_TOKEN_EXPIRE_MINUTES` and the chain length. We walk iteratively in SQL (`SELECT id, rotated_to_id, revoked_at FROM auth_session WHERE replaced_by_id IN (...)` until exhausted), capped at 100 hops as a defensive limit.

**Why DB-backed and not stateless JWT?** The spec says "refresh usado se invalida" — that requires state. Stateless refresh tokens can't be revoked without a denylist, and a denylist is the same thing as a session table without the metadata. Storing the hash in the row also gives us `last_used_at`, `ip_origen`, and the chain pointer for free.

### D3 — Password hashing and recovery token storage

**Passwords: Argon2id.** Wrapped in `core/security/passwords.py`:

```python
def hash_password(plaintext: str) -> str: ...
def verify_password(plaintext: str, hash: str) -> bool: ...
```

Parameters pinned in code: `time_cost=3`, `memory_cost=64 * 1024`, `parallelism=4`. The library's default parameters are tuned for ~50ms; pinning ours gives predictable cost across upgrades.

**Recovery tokens: opaque random + Argon2id hash at rest.**

- Token = 32 bytes from `secrets.token_urlsafe(32)`. URL-safe, no padding.
- Stored: `auth_password_reset.token_hash = argon2id(token)`, `expires_at = now() + PASSWORD_RESET_TOKEN_TTL_MINUTES`, `used_at = NULL`, `user_id`, `tenant_id`.
- The raw token is only ever returned to the user (in the email link), never persisted.
- On `POST /api/auth/reset`: Argon2id-verify the presented token against the stored hash. On match: set new password, set `used_at = now()`, revoke all active `auth_session` rows for that user (chain-walk if necessary, but the simpler `UPDATE auth_session SET revoked_at = now() WHERE user_id = X AND revoked_at IS NULL` suffices in MVP).
- Lookup strategy: the email contains a token; we don't know which user it belongs to without a lookup. Store a short "selector" prefix (`token_id_prefix`, first 8 chars of a separate UUID) on the reset row, index it, and look up by `(selector, Argon2id-verify)`. The selector is not a secret (it's already in the URL), but indexing by it gives O(1) lookup. This avoids scanning the table on every reset.

**Why both selector and Argon2id hash?** The selector gives the row to verify against; the Argon2id hash gives constant-time equality and protects the secret in the database if the DB is dumped. Without the hash, a dumped DB gives an attacker every active token. Without the selector, the lookup is O(N) and degrades with table size.

### D4 — Rate limiting: in-memory sliding window, swappable

**Backend.** In-process `dict[(ip, subject), deque[float]]` guarded by an `asyncio.Lock`. Sliding window: drop entries older than `now - LOGIN_RATE_LIMIT_WINDOW_SECONDS`, count the rest, reject if `>= LOGIN_RATE_LIMIT_PER_MINUTE`.

**Key.** `(client_ip, email_lower)`. Both are required to disambiguate: a single IP can serve many users (corp NAT), and a single email can be probed from many IPs (botnet). Including both halves the false-positive rate.

**Cleanup.** A background task that runs every 5 minutes evicts keys whose deque is empty. No persistence — process restart loses the counters, which is acceptable for a brute-force defense (worst case: a few extra login attempts in the first 60s after restart).

**Why not Redis?** Redis is not in the stack yet. Adding it for C-03 would balloon scope. The seam is the limiter's interface (`RateLimiter` Protocol with `check(key) -> bool` and `record(key) -> None`); swapping the in-memory implementation for a Redis one is a one-class change in a future ADR.

**Where it lives.** `app/core/rate_limit.py` exposes the protocol and a default `InMemorySlidingWindowRateLimiter`. The login router calls `check` first (does not record); on a successful login it calls `record` (to discount the attempt, since the request was legitimate); failed logins count toward the limit. This prevents an attacker from exhausting the budget for a legitimate user by spamming from a different IP — wait, actually that's wrong: we want to *count* failed logins, not just successful ones. The correct behavior: `check` returns whether the limit is exceeded; if not exceeded, the request proceeds. The router calls `record` regardless of outcome (success or failure), so both contribute to the limit. This is the standard approach.

### D5 — 2FA TOTP flow

**Enrollment.**

1. User authenticates (full session, no 2FA gate yet — they have no TOTP secret to verify against).
2. `POST /api/auth/2fa/enroll` generates `secret = pyotp.random_base32(32)`. Stores the secret encrypted (AAD `auth_user.totp_secret`) on the row, `totp_enabled = false`. Returns `{otpauth_uri, secret, qr_png_base64?}`.
3. The user adds the secret to their authenticator app, then calls `POST /api/auth/2fa/verify` with a 6-digit code. The service decrypts the secret, runs `pyotp.TOTP(secret).verify(code, valid_window=1)`. On match, sets `totp_enabled = true`. Emit `AUTH_2FA_ENROLL`.
4. The `secret` is **never** returned by `verify`. The `otpauth_uri` and `secret` are returned only by `enroll` (and only once — re-enrollment is a separate flow that resets the secret).

**Login.**

1. `POST /api/auth/login` with `{tenant_codigo, email, password, totp_code?}`.
2. Verify password first (Argon2id). If invalid → 401, no 2FA check, emit `AUTH_LOGIN_FAIL`.
3. If valid and `totp_enabled = false` → issue tokens.
4. If valid and `totp_enabled = true` and `totp_code` is missing → return **401 with `code = "AUTH_2FA_REQUIRED"` and a non-leaky hint**. The client prompts for the code and calls login again.
5. If valid and `totp_enabled = true` and `totp_code` is present → `pyotp.TOTP(decrypted_secret).verify(totp_code, valid_window=1)`. On match → issue tokens. On mismatch → 401 `AUTH_2FA_INVALID`, emit `AUTH_LOGIN_FAIL`.

**Why `valid_window=1`?** PyOTP's `valid_window=1` accepts the current 30s window plus the previous one, mitigating clock skew between server and authenticator. With a stricter window, users on a slow phone hit invalid codes too often. We accept the small security loss (a 30s window of replay) in exchange for UX.

**Disabling 2FA** is out of scope for C-03 (no UI, no admin flow yet); the seam is there for a later change.

### D6 — Tenant resolution on login

**`POST /api/auth/login` payload requires `tenant_codigo`.**

```json
{ "tenant_codigo": "UBA_FCEN", "email": "alice@example.com", "password": "...", "totp_code": "123456" }
```

The service resolves `tenant_id` from `tenant_codigo` (one indexed lookup). If the tenant is missing, soft-deleted, or `estado = Inactivo` → 401 with a generic `AUTH_INVALID_CREDENTIALS` (constant-time; do not leak whether the tenant exists).

**Why not subdomain or globally unique email?** Subdomains break local dev (`http://localhost:8000` has no tenant subdomain) and require DNS + reverse proxy work. Globally unique email forces a global address space, which is unrealistic in academia (the same alice works at two institutions). The `tenant_codigo` in the payload is explicit, simple, and matches the way the rest of the multi-tenant API will receive tenant hints (in the JWT, from the auth flow).

### D7 — Identity immutability and the `get_current_user` dependency

**Single resolver.** `get_current_user(request, db) -> CurrentUser`:

1. Read `Authorization: Bearer <token>`.
2. If absent or malformed → 401 `AUTH_TOKEN_MISSING`.
3. Decode via `core/security/jwt.py:decode_access_token(token)`. Verifies signature, `exp`, `iat`, `typ="access"`. On any failure → 401 (specific code depending on the failure).
4. Load the `auth_user` by `sub`. If not found or `deleted_at IS NOT NULL` or `is_active = false` → 401 `AUTH_TOKEN_REVOKED`.
5. Load the `auth_session` by `sid`. If `revoked_at IS NOT NULL` → 401 `AUTH_TOKEN_REVOKED`.
6. **Assert** `auth_user.tenant_id == auth_session.tenant_id` and the session's `tenant_id` matches the requested tenant context.
7. Build a `CurrentUser(user_id, tenant_id, session_id, is_2fa_verified)` value object.
8. Set the `TenantContext` (with `is_impersonating=False`; C-05 will introduce impersonation) on the per-task `ContextVar`.
9. Return the `CurrentUser`.

**Identity is never read from a request parameter.** A request like `GET /api/foo?as_user_id=...` does nothing — the parameter is ignored entirely. Tests in `tests/auth/test_identity_immutability.py` enumerate the surfaces (query, body, header, path) and assert the resolver ignores them.

**`get_optional_current_user`** does the same but returns `None` on missing/invalid token. No endpoint in C-03 uses it, but C-21 will need it for the login page itself (which must be reachable anonymously).

### D8 — Code layout and file ownership

```
backend/app/
  auth/                                 # NEW: auth subsystem
    __init__.py
    deps.py                             # get_current_user, get_optional_current_user
    models.py                           # AuthUser, AuthSession, AuthPasswordReset
    repositories.py                     # AuthUserRepository, AuthSessionRepository, AuthPasswordResetRepository
    services/
      __init__.py
      auth_service.py                   # login, refresh, logout
      password_reset_service.py         # forgot, reset
      two_factor_service.py             # enroll, verify
    routers/
      __init__.py
      auth.py                           # POST /api/auth/login, refresh, logout
      password_reset.py                 # POST /api/auth/forgot, reset
      two_factor.py                     # POST /api/auth/2fa/enroll, verify
    schemas.py                          # Pydantic DTOs (extra='forbid')
    errors.py                           # error codes + HTTPException factory
  core/
    dependencies.py                     # MOD: tenant_context_dep now JWT-driven
    config.py                           # MOD: 5 new settings
    security/
      __init__.py
      crypto.py                         # (unchanged from C-02)
      passwords.py                      # NEW: Argon2id wrapper
      jwt.py                            # NEW: encode/decode/verify
    rate_limit.py                       # NEW: RateLimiter protocol + InMemorySlidingWindowRateLimiter
  api/v1/
    main_router.py                      # MOD: include auth, password_reset, two_factor routers
  integrations/
    email.py                            # NEW: dispatch_email seam (stub for C-03)
alembic/versions/
  002_auth_user_auth_session_auth_password_reset.py   # NEW: one migration, three tables
tests/
  auth/
    __init__.py
    conftest.py                         # fixtures: test client, test DB, test tenant, test user, JWT minting helper
    test_login.py
    test_refresh_rotation.py
    test_logout.py
    test_password_recovery.py
    test_two_factor.py
    test_rate_limit.py
    test_identity_immutability.py
    test_get_current_user.py
  core/
    test_jwt.py
    test_passwords.py
    test_rate_limit.py
```

The router module count is high but each is short (≤200 LOC), aligned with the project rule.

### D9 — Migration ordering and C-07 handoff

**In C-03**, the migration creates:

- `auth_user (id, tenant_id, email_enc, password_hash, totp_secret_enc, totp_enabled, is_active, failed_login_count, last_login_at, created_at, updated_at, deleted_at)` with indexes `(tenant_id, email_enc)`, `(tenant_id, deleted_at)`.
- `auth_session (id, tenant_id, user_id FK, refresh_token_hash, jti UNIQUE, issued_at, expires_at, last_used_at, revoked_at, ip_origen, user_agent, rotated_to_id FK, replaced_by_id FK, created_at, updated_at, deleted_at)` with indexes `(user_id, revoked_at)`, `(tenant_id, deleted_at)`, `(jti)`.
- `auth_password_reset (id, tenant_id, user_id FK, selector, token_hash, expires_at, used_at, created_at, deleted_at)` with indexes `(selector)`, `(user_id)`, `(tenant_id, deleted_at)`.

**In C-07**, the options are:

- **(a) Add columns to `auth_user`**, rename to `usuario`, migrate the data. PII columns (`dni_enc`, `cuil_enc`, `cbu_enc`, `alias_cbu_enc`, `legajo`, `nombre`, `apellido`) are added. `email_enc` is preserved (or migrated to a new column). `auth_session.user_id` and `auth_password_reset.user_id` are renamed to `usuario_id` via a separate migration.
- **(b) Keep `auth_user` as the credential slice**, create a sibling `usuario` table with a 1:1 FK to `auth_user.id`, and reference `usuario.id` from `asignacion`. C-07 picks whichever is cleaner once `Usuario` semantics are firmed up.

C-03 does not pick (a) vs (b). It only guarantees that:

- `auth_user.id` is a stable UUID.
- The `email` field is in `auth_user.email_enc` (so login works without a join to `usuario`).
- The `password_hash` is in `auth_user` (login does not need `Usuario`).
- `asignacion` (C-07) can reference either `auth_user.id` or a future `usuario.id` — both are valid targets.

The naming `auth_*` is intentional: it signals "credential slice owned by the auth subsystem" and gives C-07 a clean rename story.

### D10 — Test database and isolation

Tests use the same `DATABASE_URL_TEST` already wired by C-01/C-02. Each test gets a fresh schema via `Base.metadata.create_all` (or, faster, a transactional rollback per test). The C-02 test fixtures (`tests/conftest.py`) are extended; the C-02 `X-Tenant-Id` header tests are migrated to set the context via a fixture that calls `set_tenant_context(TenantContext(tenant_id=...))` directly, since the header is gone.

**No DB mocks.** Every test that exercises an endpoint hits the real PostgreSQL. Rate-limit tests hit the in-memory limiter directly (it's pure code, no DB).

**Identity-immutability tests** enumerate the surfaces (query, body, header, path, cookie) and the values an attacker might try (`as_user_id`, `tenant_id`, `X-Impersonate-User`, etc.) and assert the resolver ignores all of them. The test is named `test_get_current_user_ignores_request_supplied_identity`.

## Risks / Trade-offs

- **[In-memory rate limit doesn't survive restart]** → Mitigation: documented in ADR-lite in the rate-limit module; restart costs at most `LOGIN_RATE_LIMIT_PER_MINUTE` extra attempts per `(ip, email)` in the next 60s. Acceptable for MVP; Redis upgrade is a one-class swap.
- **[Email seam is stubbed in C-03]** → Mitigation: the `dispatch_email` interface is the only thing later changes need to implement. The test collector captures what would have been sent; tests can assert the link is correct without a real SMTP server. No production user exists yet (no `Usuario`, no tenants in production), so the absence of real email is not a runtime risk for C-03.
- **[TOTP `valid_window=1` accepts a 30s replay window]** → Mitigation: standard for TOTP UX; the spec accepts the trade-off. A future change can tighten it if institutional policy demands.
- **[Recovery email enumeration]** → Mitigation: `POST /api/auth/forgot` returns 200 with a generic body regardless of whether the email exists; the response time is also constant-padded to ~200ms. This is the best we can do without confirming a real email.
- **[C-07 may rename `auth_user` to `usuario` or add columns]** → Mitigation: the schema and service layer are designed so either path is a single Alembic migration. The C-03 README in the change notes the two paths for C-07 to choose from.
- **[Single-tenant password reset revoke is `UPDATE … WHERE user_id = X AND revoked_at IS NULL`, not a chain walk]** → Mitigation: this revokes all **active** sessions. Sessions already past expiry are no threat. Chain walks are reserved for reuse detection, where a precise traversal is required. Documented in `auth_session_service._revoke_active_for_user`.
- **[C-02 tests using `X-Tenant-Id` need migration]** → Mitigation: a single fixture in `tests/conftest.py` (`auth_jwt_test_user`) that mints a JWT for a known user and a known tenant, plus a `set_tenant_context` fixture. The change to the C-02 test suite is mechanical and listed in tasks.
- **[Failed-login count and account lockout]** → Out of scope. Rate limit is the brute-force defense. `failed_login_count` is recorded but not enforced in C-03; C-07 or a later hardening change will use it.

## Migration Plan

**Deployment (single step, no schema migration of pre-existing data):**

- C-03 introduces three new tables. There is no pre-existing data to migrate.
- The C-02 placeholder `tenant_context_dep` is replaced in the same release. The header path is deleted; any test or smoke script that relied on it is updated to either mint a JWT (preferred) or use the `set_tenant_context` fixture (for service-level tests that don't go through HTTP).
- The five new env vars have defaults; existing `.env` files work without change.
- The `audit_emit` seam is extended with new action codes; existing C-02 audit emissions continue to work. The seam logs a WARNING for unknown codes — that WARNING is expected in C-03 and reviewed as "this is the change that introduces them."

**Rollback:**

- Revert the merge commit. The three new tables drop on Alembic downgrade; nothing in pre-C-03 code referenced them.
- The `tenant_context_dep` swap is also reverted, restoring the `X-Tenant-Id` placeholder. C-02 smoke tests pass again. No data is lost.

**C-07 handoff:**

- The auth subsystem's `AuthUser` and `AuthSession` rows are stable in C-03 and C-04. C-07 introduces `Usuario` (PII completa) and `Asignacion` (vigencia) on top of C-04.
- Two viable paths for C-07 (documented in D9, decided in C-07's design, not C-03's):
  - (a) Rename `auth_user` → `usuario`, add PII columns, keep credential fields.
  - (b) Add a sibling `usuario` table with 1:1 FK to `auth_user.id`.
- C-03 does not pick (a) vs (b); it leaves the seam clean and the README explicit.

## Open Questions

1. **Should `/api/auth/login` return the user's roles in the response when 2FA is disabled?** The token omits roles (D1), so the client must call a `GET /api/me` to know what to render. That endpoint is in C-21, not C-03. **Decision:** the login response returns `access_token`, `refresh_token`, `expires_in`, `token_type`, and `requires_2fa: false` only. C-21 calls `GET /api/me` after login. **No open question; documented for visibility.**
2. **CORS and cookie strategy.** C-03 issues bearer tokens in the response body. C-21 will store them in memory (not localStorage, to avoid XSS). The cookie strategy is owned by C-21. **No open question for C-03.**
3. **Audit emission for failed login: do we record the attempted email?** The PII rule says no plaintext in audit. We record `email_hash` (SHA-256 of the lowercased email) for correlation without leaking. **Decision recorded in tasks; no open question.**
4. **Should the rate limiter key include `tenant_codigo`?** Different tenants have different `client_ip`+`email` collisions. Including `tenant_codigo` in the key would isolate them, but the payload is just rate-limited; an attacker can spam with any `tenant_codigo`. **Decision: key is `(client_ip, email_lower)` only.** The tenant is checked for validity on top; the rate limit fires before the tenant lookup is even considered, which is the right order (don't leak tenant-existence via timing). **No open question.**
5. **What happens if the `audit_emit` seam raises?** The seam never raises today (it logs a WARNING and returns). If a future change makes it strict, every auth call could fail. **Decision: the seam stays non-raising; C-03 wraps each emit in a try/except that logs but does not propagate.** **No open question; documented for future-proofing.**
6. **Refresh-token TTL.** Default 7 days feels long for a school context. The project rule is "configurable, sensible default." **Decision: default 7 days, env-overridable.** A future change can shorten it for specific tenants. **No open question.**
7. **The `auth_user.email_enc` field vs `Usuario.email_enc` in C-07.** C-03 owns the email in `auth_user`. If C-07 chooses option (a) (rename and add columns), the email column is preserved. If C-07 chooses (b) (sibling), `auth_user.email_enc` remains. Either way, login works in C-03 and C-07+ without a re-architecture. **No open question for C-03.**
