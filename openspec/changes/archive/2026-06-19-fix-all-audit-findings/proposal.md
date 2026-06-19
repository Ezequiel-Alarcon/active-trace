## Why

A comprehensive backend audit uncovered 25 TODO markers across 20 files representing real bugs and quality issues. These include critical authz bypasses (bare `require_permission()` calls without `Depends()`), architecture violations (direct DB queries in routers/services, hard deletes, unencrypted PII), infrastructure gaps (missing security middleware), and domain-level bugs (missing field validation, stale KB docs). These defects violate the project's hard rules and will fail code review. Fixing them now prevents regressions as the codebase grows.

## What Changes

- Wrap all bare `require_permission()` calls with `Depends()` in route decorators across 4 files
- Fix `PermissionResolver.resolve()` to filter by user, temporal validity, and soft-delete
- Make `audit_emit()` write to DB via AuditLogRepository instead of logger
- Move direct DB queries from routers to services and from services to repositories
- Replace hard delete with soft delete in LiquidacionRepository
- Encrypt `Comunicacion.destinatario` following Usuario's email_hash/email_enc pattern
- Fix refresh token rotation to generate new tokens and add reuse detection
- Add TrustedHostMiddleware and security headers middleware to app
- Conditionally disable OpenAPI docs in production
- Add `estado` field to Usuario model
- Add RN-26 banking data validation in liquidaciones
- Rename `facturante` → `facturador` or add alias with documented decision
- Define NEXO role permissions or document as blocked
- Implement RN-01 `(Real)` column suffix detection
- Enforce RN-16 preview-before-send for comunicaciones
- Fix AuditLogRepository `deleted_at` column mismatch
- Update RN-05 in KB to match versioned padron (non-destructive)

## Capabilities

### New Capabilities

No new capabilities — this is a cross-cutting bugfix/quality change. Each fix corrects an existing capability's implementation to match its spec.

### Modified Capabilities

- `rbac-require-permission-guard`: Fix bare `require_permission()` calls to use `Depends()` — the guard was not being invoked
- `rbac-permission-resolution`: Fix `PermissionResolver.resolve()` to filter by user identity and temporal validity
- `soft-delete`: Fix LiquidacionRepository hard delete; fix AuditLogRepository deleted_at mismatch
- `pii-encryption`: Encrypt Comunicacion.destinatario (email_hash + email_enc)
- `usuario-crud`: Add `estado` field to Usuario model
- `auth-jwt-2fa`: Fix refresh token rotation with new token generation and reuse detection
- `observability-base`: Make audit_emit() persistent (DB writes instead of logger)

## Impact

- **Security**: Closes authz bypasses that allowed unguarded permission checks; encrypts PII in comunicaciones; adds defense-in-depth middleware
- **Architecture**: Restores Clean Architecture layering (Routers → Services → Repositories) in affected files
- **Data integrity**: Hard delete → soft delete prevents data loss; audit trail becomes persistent
- **KB/docs**: RN-05 corrected to match implementation; NEXO role decision documented
- **Files touched**: ~20 source files across auth, rbac, core, repositories, services, models, and API v1 routers
- **Dependencies**: No new dependencies — uses existing crypto, repository, and audit infrastructure
