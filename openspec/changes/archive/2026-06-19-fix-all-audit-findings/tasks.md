## 1. A — CRITICAL: Authz bypasses

- [x] 1.1 A1: Fix `require_permission()` calls in `app/api/v1/analisis.py` — wrap 4 bare calls with `dependencies=[Depends(require_permission(...))]` in route decorators
- [x] 1.2 A1: Fix `require_permission()` calls in `app/api/v1/calificaciones.py` — wrap 5 bare calls
- [x] 1.3 A1: Fix `require_permission()` calls in `app/api/v1/umbral_materia.py` — wrap 3 bare calls
- [x] 1.4 A1: Fix `require_permission()` calls in `app/modules/comunicacion/router.py` — wrap 6 bare calls
- [x] 1.5 A2: Fix `PermissionResolver.resolve()` in `app/rbac/services.py` — add join with Asignacion, filter by user_id, temporal validity (desde/hasta), and deleted_at
- [x] 1.6 A3: Fix `audit_emit()` in `app/core/audit.py` — replace `logger.warning()` with `AuditLogRepository.create()`, make async, accept db session
- [x] 1.7 A3: Update all callers of `audit_emit()` to pass DB session (padron.py, equipos.py, auth_service.py, etc.)

## 2. B — HIGH: Architecture violations

- [x] 2.1 B1: Move `_tenant_lookup()` DB query from `app/auth/routers/auth.py` to `AuthService`
- [x] 2.2 B2: Move direct `session.execute()` from `app/services/guardias.py` to `GuardiaRepository`
- [x] 2.3 B2: Move direct `session.execute()` from `app/services/padron.py` to `PadronRepository`
- [x] 2.4 B2: Move direct `session.execute()` from `app/services/evaluaciones.py` to `ColoquioRepository`
- [x] 2.5 B2: Move direct `session.execute()` from `app/auth/services/auth_service.py` to `AuthSessionRepository`
- [x] 2.6 B3: Fix hard delete in `app/repositories/liquidaciones.py` — replace `delete()` with `update()` setting `deleted_at` and `deleted_by`
- [x] 2.7 B4: Encrypt `Comunicacion.destinatario` — add `email_hash` + `email_enc` columns to model, create Alembic migration
- [x] 2.8 B5: Fix refresh token rotation in `app/auth/services/auth_service.py` — generate new token on each rotation, add reuse detection

## 3. C — HIGH: Infrastructure hardening

- [x] 3.1 C1: Add `TrustedHostMiddleware` to `app/main.py` with configurable allowed hosts
- [x] 3.2 C2: Add security headers middleware to `app/main.py` (X-Content-Type-Options, X-Frame-Options, HSTS, CSP)
- [x] 3.3 C3: Conditionally disable OpenAPI docs in production (`docs_url=None`, `redoc_url=None` when `ENVIRONMENT=production`)

## 4. D — HIGH/MEDIUM: Domain gaps

- [x] 4.1 D1: Add `estado` field to `Usuario` model with default `"activo"`, create Alembic migration
- [x] 4.2 D2: Add RN-26 banking data validation in liquidaciones service/repository
- [x] 4.3 D3: Rename `facturante` to `facturador` or add alias across codebase; document decision in code comment
- [x] 4.4 D4: Define NEXO role permissions in the permission catalogue or document as blocked with `# TODO:` marker
- [x] 4.5 D5: Implement RN-01 `(Real)` column suffix detection in padron import logic
- [x] 4.6 D6: Enforce RN-16 preview-before-send in comunicaciones flow
- [x] 4.7 D7: Fix `AuditLogRepository` `deleted_at` column mismatch (rename or align column)

## 5. E — KB Contradiction

- [x] 5.1 E1: Update RN-05 in `knowledge-base/05_reglas_de_negocio.md` to match E6 (versioned padron, not destructive)
