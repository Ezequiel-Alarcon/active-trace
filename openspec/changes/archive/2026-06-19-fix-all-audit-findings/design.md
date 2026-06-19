## Context

A systematic audit of the backend codebase revealed 25 TODO markers across 20 files. These are bugs, not style issues — they include authz bypasses (require_permission called as a regular function instead of a FastAPI dependency, so the permission check never executes), database queries in routers and services that should go through repositories, hard deletes violating the soft-delete rule, unencrypted PII in the comunicaciones model, and a broken audit_emit() that logs to console instead of persisting to the database. All items are documented in the codebase via `# TODO:` markers per project hard rule #17.

## Goals / Non-Goals

**Goals:**
- Close all authz bypasses by wiring require_permission as proper FastAPI dependencies
- Restore layered architecture: move DB queries from routers/services to repositories
- Make audit_emit() persistent (DB writes via AuditLogRepository)
- Fix soft-delete violations (LiquidacionRepository, AuditLogRepository)
- Encrypt PII in Comunicacion.destinatario
- Fix refresh token rotation with reuse detection
- Add infrastructure hardening (TrustedHostMiddleware, security headers, conditional OpenAPI)
- Fix domain gaps (estado field, RN-26 validation, RN-01 Real suffix, RN-16 preview)
- Sync KB RN-05 with implementation

**Non-Goals:**
- No new features or capabilities
- No schema migrations for existing models (estado field excluded — needs migration)
- No refactoring beyond the specific TODO items
- No frontend changes

## Decisions

### D1: require_permission fix — `dependencies=[Depends(...)]` in decorator

**Decision**: Fix bare `require_permission("modulo:accion")` calls by moving the permission check into the route decorator's `dependencies` parameter as `dependencies=[Depends(require_permission("modulo:accion"))]`.

**Rationale**: Bare `require_permission(...)` returns a `PermissionChecker` class (not a callable). FastAPI never invokes it because it's not wired through `Depends()`. The `dependencies=[Depends(...)]` approach is the canonical FastAPI pattern for guard-style middleware. An alternative of using a wrapper function or APIRouter dependency was considered but rejected — per-route dependencies are more explicit and easier to audit.

**Files affected**: `app/api/v1/analisis.py` (4 calls), `app/api/v1/calificaciones.py` (5 calls), `app/api/v1/umbral_materia.py` (3 calls), `app/modules/comunicacion/router.py` (6 calls).

### D2: PermissionResolver.resolve() — add user/temporal filtering

**Decision**: Add an inner join with `AsignacionRole` (through the `Asignacion` model), filter by `user_id`, check `desde <= now <= hasta`, and exclude soft-deleted rows (`deleted_at IS NULL`).

**Rationale**: The current `resolve()` performs a raw query that returns all role-permission mappings without scoping to the requesting user. This means any authenticated user gets all permissions. The join with Asignacion is the correct tenant-aware lookup path.

### D3: audit_emit() — write to DB via AuditLogRepository

**Decision**: Replace `logger.warning(...)` with `AuditLogRepository.create(session, ...)`. Make `audit_emit()` async, accept a `db: AsyncSession` parameter (or fall back to a background task if no session available).

**Rationale**: The audit log must be append-only and persistent. Logging to console loses data on restart and cannot be queried. Using the existing AuditLogRepository ensures consistent write patterns. The caller must pass an active DB session.

### D4: Refresh token rotation — new token + reuse detection

**Decision**: On each refresh, generate a completely new JWT refresh token (not re-sign the old one). Store the new token hash in DB, invalidate the old one. If an already-revoked token is presented, revoke ALL refresh tokens for that user (reuse detection).

**Rationale**: This follows RFC 6749 and OAuth 2.0 best practices. Reuse detection prevents stolen refresh token attacks.

### D5: Comunicacion.destinatario encryption

**Decision**: Add `email_enc` (AES-256 encrypted bytes) and `email_hash` (SHA-256 HMAC) columns to `Comunicacion`, exactly mirroring the pattern in `Usuario` model. The plaintext `destinatario` field is replaced by these.

**Rationale**: Reusing the existing PII encryption infrastructure avoids introducing new crypto primitives. The `email_hash` enables lookups without decryption.

### D6: Soft delete in LiquidacionRepository

**Decision**: Replace `session.execute(delete(Liquidacion).where(...))` with `session.execute(update(Liquidacion).where(...).values(deleted_at=func.now(), deleted_by=user_id))`.

**Rationale**: Hard Rule #13 mandates soft delete everywhere. This was an oversight.

### D7: Security middleware

**Decision**: Add `TrustedHostMiddleware(allowed_hosts=...)` and a custom `SecurityHeadersMiddleware` that sets `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security: max-age=31536000; includeSubDomains`, and `Content-Security-Policy`. Disable OpenAPI docs (`docs_url=None`, `redoc_url=None`) when `ENVIRONMENT=production`.

**Rationale**: Defense-in-depth. These are standard production hardening measures with zero behavioral impact on API responses.

### D8: KB RN-05 contradiction

**Decision**: Update RN-05 in `knowledge-base/05_reglas_de_negocio.md` to match the existing E6 implementation: padron is versioned-append, not destructive-replace.

**Rationale**: The KB is the source of truth. The implementation is already correct; the doc is stale.

## Risks / Trade-offs

- **Authz bypass fix** — Low risk. The `dependencies=[Depends(...)]` pattern is well-tested. Regression: some routes may have relied on the bypassed check, but those routes would return 403 after fix. This is correct behavior.
- **audit_emit() async** — Callers must now handle async. If any sync context calls audit_emit(), wrap in a background task. Risk: missing audit events during transition.
- **Refresh token reuse detection** — If a legitimate user's token is revoked due to a race condition, they get logged out. Mitigation: add a short grace window (30s) before revoking all tokens.
- **Comunicacion migration** — Adding columns to an existing model requires an Alembic migration. Existing data must be backfilled.
- **estado field** — Requires a new Alembic migration with a default value for existing rows.
