# Design: C-04 — RBAC Permisos Finos

## Context

C-03 (auth-jwt-2fa) introduced `get_current_user`: given a bearer token, it returns the authenticated `AuthUser` row with `user_id` and `tenant_id`. Identity is solved. Authorization is not — the system has no concept of what an authenticated user *can do*.

Every endpoint in the system (C-05 audit-log, C-06 estructura-academica, etc.) needs to declare a required permission and have that permission checked against the user's effective set. The permission model must be:
- **Multi-tenant**: roles and permissions are scoped to a tenant — no cross-tenant permission leakage.
- **Administrable**: the permission matrix lives in the DB, not hardcoded. ADMIN can manage it.
- **Server-side resolved**: roles are NOT in the JWT. Putting them in the token would force re-login every time a COORDINADOR assigns a new role — hostile UX for a frequently-changing setup.
- **Efficient**: permission resolution must not hit the DB on every request. Cache per-request or per-session.

The current codebase has:
- `app/core/permissions.py`: placeholder (C-01 reserved for C-04)
- `app/core/dependencies.py` line 82: `require_permission` stub reserved for C-04
- No role or permission tables exist yet.

---

## Goals / Non-Goals

**Goals:**
- Three tables: `rol`, `permiso`, `rol_permiso` — all tenant-scoped.
- Seed data: 7 domain roles × full permission matrix from `knowledge-base/03_actores_y_roles.md` §3.3.
- `PermissionResolver` service: computes effective permissions per user per request as the union of all role permissions, scoped to tenant.
- `require_permission("modulo:accion")` FastAPI dependency: checks effective permissions; 403 if missing.
- Admin catalog API: CRUD for roles and permissions, attach/detach permission↔role.
- Migration 002: tables + indexes + seed.

**Non-Goals:**
- Impersonation (`impersonacion:usar`) — owned by C-05.
- Assignment validity window enforcement — owned by C-07. C-04 seeds the matrix; temporal validity is out of scope.
- Roles in the JWT — rejected (forces re-login on role changes).
- Hardcoded fallback permissions — rejected (must be data).
- Direct `RolPermiso` manipulation by non-admin users — rejected (catalog management is admin-only).

---

## Decisions

### D1: Roles not in JWT

**Decision**: Roles are resolved server-side from the DB on each request (or from a request-scoped cache). The JWT carries `sub` (user_id), `tid` (tenant_id), and `sid` (session_id) only.

**Rationale**: C-02/C-03 already decided this (ADR). Roles in the JWT force re-login on every role assignment/ revocation. A COORDINADOR frequently assigns PROFESOR to a user mid-cuatrimestre — forcing re-login every time is unacceptable UX. Server-side resolution is the right model.

**Alternatives considered**:
- B (roles in JWT): rejected — re-login on role change.
- C (roles in JWT + short TTL): rejected — complexity and UX cost.

### D2: Tenant-scoped tables (not roles catalog per tenant)

**Decision**: `rol`, `permiso`, `rol_permiso` each carry `tenant_id`. The seed creates the same roles and permissions in every tenant (universal baseline). Tenants can customize (add roles, add permissions, change the matrix).

**Rationale**: The 7 domain roles are universal. If a tenant needs a custom role, they create it under their `tenant_id`. No cross-tenant pollution.

**Alternatives considered**:
- B (global roles catalog, tenant overrides): rejected — too complex for v1.
- C (per-tenant clone on tenant creation): would be C-07's problem. C-04 seeds the global baseline.

### D3: In-request cache for permission resolution

**Decision**: `PermissionResolver` is instantiated per-request and caches the resolved set in the request state. The cache key is `(user_id, tenant_id)`. Cache lifetime = request lifecycle (not session). No Redis/memcached needed — Python dict on the resolver instance.

**Rationale**: Permission resolution requires 1 DB query (fetch user's roles + their permissions). At ~1000 req/s, that's 1000 queries/s if uncached. At request-scoped cache, it's 1 query per user per request. For a single user's page load that hits 5 endpoints, only 1 resolution call is needed (subsequent calls reuse the cached set from request state).

**Trade-off**: Cache is not shared across requests. A role change takes effect on the user's next request (not instantaneous). This is acceptable — the system is not financial-grade real-time.

**Alternatives considered**:
- B (Redis shared cache): rejected — adds infrastructure complexity. Request-scoped is sufficient.
- C (JWT claims for permissions): already rejected in D1.

### D4: `require_permission` as FastAPI dependency

**Decision**: `require_permission(permission: str)` is a FastAPI `Depends()` that:
1. Reads `current_user` from `get_current_user` (already in request state).
2. Calls `PermissionResolver.resolve(user_id, tenant_id)` (cached per-request).
3. Checks if `permission` is in the resolved set.
4. Returns `403 Forbidden` with `{"detail": "No tiene el permiso: {permission}"}` if missing.
5. If granted, attaches `current_user` + `resolved_permissions` to the request state for use by the endpoint.

**Rationale**: Every protected endpoint declares its required permission as a decorator/parameter. The check is centralized in one place, not scattered across services. Fail-closed: no declared permission → 403 by default.

### D5: Admin catalog endpoints under `admin:gestionar_roles`

**Decision**: All catalog management endpoints (create role, create permission, attach, detach) require `admin:gestionar_roles` permission. Regular users cannot manage the catalog.

**Rationale**: Admin-only operations. The permission itself is declared on the router level.

### D6: Migration 002 with seed as Alembic operations

**Decision**: Migration 002 creates `rol`, `permiso`, `rol_permiso` tables with indexes and a `bulk_insert` of the seed data (7 roles × full matrix). Implemented as an Alembic migration with raw SQL for the bulk insert (not ORM — faster and explicit).

**Rationale**: All schema changes go through Alembic. Seed as data migration (not code) ensures it runs on any environment `alembic upgrade head`.

---

## Data Model

```
Table: rol
  - id: UUID (PK)
  - tenant_id: UUID (FK → tenant.id, NOT NULL)
  - nombre: VARCHAR(64) (NOT NULL) — e.g., "ADMIN", "PROFESOR"
  - descripcion: VARCHAR(255)
  - created_at, updated_at, deleted_at
  UNIQUE (tenant_id, nombre)

Table: permiso
  - id: UUID (PK)
  - tenant_id: UUID (FK → tenant.id, NOT NULL)
  - modulo: VARCHAR(64) (NOT NULL) — e.g., "calificaciones", "equipos"
  - accion: VARCHAR(64) (NOT NULL) — e.g., "importar", "ver"
  - created_at, updated_at, deleted_at
  UNIQUE (tenant_id, modulo, accion)

Table: rol_permiso
  - id: UUID (PK)
  - tenant_id: UUID (FK → tenant.id, NOT NULL)
  - rol_id: UUID (FK → rol.id, NOT NULL)
  - permiso_id: UUID (FK → permiso.id, NOT NULL)
  - created_at
  UNIQUE (tenant_id, rol_id, permiso_id)
```

Indexes:
- `ix_rol_tenant_nombre` on `rol(tenant_id, nombre)` — unique constraint backing
- `ix_permiso_tenant_modulo_accion` on `permiso(tenant_id, modulo, accion)` — unique constraint backing
- `ix_rol_permiso_tenant_rol` on `rol_permiso(tenant_id, rol_id)`
- `ix_rol_permiso_tenant_permiso` on `rol_permiso(tenant_id, permiso_id)`

---

## Seed Data

7 roles × permission matrix from KB §3.3. Each `(tenant_id, rol, [permisos])` entry inserted as raw SQL in migration 002.

Roles: ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS.

Permissions (modulo:accion format):
- `academico:ver_estado_propio`
- `evaluaciones:reservar`
- `avisos:confirmar`
- `calificaciones:importar`
- `calificaciones:ver`
- `atrasados:ver`
- `entregas:ver_sin_corregir`
- `comunicacion:enviar`
- `comunicacion:aprobar`
- `encuentros:gestionar`
- `encuentros:registrar_guardia`
- `tareas:gestionar`
- `avisos:publicar`
- `equipos:asignar`
- `estructura:gestionar`
- `usuarios:gestionar`
- `auditoria:ver`
- `impersonacion:usar`
- `finanzas:operar_grilla`
- `finanzas:cerrar_liquidacion`
- `finanzas:gestionar_facturas`
- `tenant:configurar`
- `roles:gestionar` (admin catalog management)

---

## API Design

### Permission resolution (internal)

```
PermissionResolver.resolve(user_id: UUID, tenant_id: UUID) → set[str]
  Cache key: (user_id, tenant_id)
  Query: SELECT p.modulo, p.accion
         FROM rol_permiso rp
         JOIN rol r ON r.id = rp.rol_id
         JOIN permiso p ON p.id = rp.permiso_id
         WHERE r.id IN (SELECT rol_id FROM asignacion WHERE usuario_id = user_id AND tenant_id = tenant_id)
           AND rp.tenant_id = tenant_id
           AND p.tenant_id = tenant_id
           AND r.deleted_at IS NULL
  Returns: {f"{p.modulo}:{p.accion}" for each row}
```

**Note on assignment validity**: C-07 owns the `asignacion.vigencia` logic. For C-04, the seed uses all roles with no temporal filter. The query intentionally does NOT filter by `asignacion.desde/hasta` — that comes in C-07. C-04 always resolves all roles a user has (unfiltered). C-07 will add the temporal filter.

### Admin endpoints

```
GET    /api/admin/roles        — list roles (requires: admin:gestionar_roles)
POST   /api/admin/roles        — create role (requires: admin:gestionar_roles)
GET    /api/admin/roles/{id}   — get role detail (requires: admin:gestionar_roles)
PATCH  /api/admin/roles/{id}   — update role (requires: admin:gestionar_roles)
DELETE /api/admin/roles/{id}   — soft-delete role (requires: admin:gestionar_roles)

GET    /api/admin/permisos     — list permissions (requires: admin:gestionar_roles)
POST   /api/admin/permisos     — create permission (requires: admin:gestionar_roles)

POST   /api/admin/roles/{rol_id}/permisos/{permiso_id}  — attach (requires: admin:gestionar_roles)
DELETE /api/admin/roles/{rol_id}/permisos/{permiso_id}  — detach (requires: admin:gestionar_roles)
GET    /api/admin/roles/{rol_id}/permisos               — list permissions of a role (requires: admin:gestionar_roles)
```

### Public endpoint (no auth required)

```
GET /api/permissions/me         — return current user's effective permissions (auth required, no specific permission)
```

---

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Role change not reflected instantly (cache is request-scoped) | Acceptable for v1. User's next request gets the new permissions. No session-level cache. |
| Performance: permission resolution hits DB on first request per user per request | Request-scoped cache (dict on resolver instance). 1 query per user per request regardless of how many endpoints are called. |
| Tenant isolation: accidental cross-tenant permission leak | All queries filter by `tenant_id` explicitly. Repository pattern enforces scope. Tests cover cross-tenant scenarios. |
| Seed data drift: domain roles change in KB but not in DB | Seed is a migration operation, not a fixture. Run `alembic upgrade head` to get latest seed. On migration, seed is idempotent (upsert or clean insert with DELETE first). |
| Admin creates a role with zero permissions | Valid state. No enforcement that a role must have at least one permission. |
| Soft-delete a role that has active assignments | Role's `deleted_at` is set. Existing assignments remain (C-07's problem). The role's permissions are still resolved for users with that assignment until the assignment itself is ended (C-07). |

---

## Migration Plan

1. Generate migration 002: creates `rol`, `permiso`, `rol_permiso` tables + indexes + seed.
2. Run `alembic upgrade head` — tables created + seed applied.
3. Verify: `SELECT COUNT(*) FROM rol` returns 7.
4. Deploy app with C-04 code (guard, resolver, admin endpoints).
5. Rollback: `alembic downgrade` — drops tables (CASCADE). Data loss if rollback after production data exists — acceptable at v1.

---

## Open Questions

| Question | Status |
|----------|--------|
| Q1: Should `permiso` be unique per tenant globally, or can two tenants have a permission with the same `(modulo, accion)` but different descriptions? | Resolved: yes, unique per tenant. Different tenants can have same `modulo:accion` with different descriptions (description is non-critical metadata). |
| Q2: Should the seed be tenant-specific or universal? | Resolved: universal baseline. Every tenant gets the 7 roles + full matrix on creation. Tenant customization (add/remove) is their own responsibility. |
| Q3: What happens when ADMIN deletes a domain role (e.g., PROFESOR)? | Out of scope for C-04. Soft-delete leaves the row but marks deleted. C-07's assignment logic handles what happens when a user loses a role. |