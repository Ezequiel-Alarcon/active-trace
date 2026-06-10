# Proposal: C-04 — RBAC Permisos Finos

## Why

C-03 (auth-jwt-2fa) introduced the authentication layer: `get_current_user` resolves identity and tenant from the JWT. **But identity alone is not authorization.** Every endpoint in the system needs to declare what permission it requires — and the system needs a resolvable, administrable permission model. Without C-04, the app has auth without authorization: any authenticated user can hit any endpoint. C-04 closes that gap by building the RBAC layer (roles, permissions, matrix, server-side resolution, `require_permission` guard) that every subsequent change depends on.

> ⚠️ This is a **CRÍTICO** change — auth, multi-tenancy, RBAC, and audit are governance CRÍTICO. No code written without explicit human approval.

---

## What Changes

- **New tables**: `Rol` (name, description, tenant_id), `Permiso` (modulo, accion, tenant_id), `RolPermiso` (rol_id, permiso_id, tenant_id — many-to-many with tenant scope).
- **Seed data**: 7 domain roles (ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS) with the full permission matrix from `knowledge-base/03_actores_y_roles.md` §3.3 as initial data (not hardcoded — in the DB).
- **Permission resolution**: `PermissionResolver` service that computes effective permissions per user per request by unioning all roles' permissions, scoped to tenant. Resolution is server-side; roles are NOT in the JWT (C-02/C-03 ADR decision).
- **`require_permission("modulo:accion")` guard**: FastAPI dependency that checks the user's effective permissions. Without it → 403 Forbidden.
- **Catalog management**: CRUD endpoints for roles and permissions (ADMIN only) — read-only for most; no endpoint exposes raw `RolPermiso` manipulation.
- **Migration 002**: `rol`, `permiso`, `rol_permiso` tables + seed.
- **No role-in-token**: Roles are resolved server-side per request from the DB cache. Putting them in the JWT would force re-login on every role change.

---

## Capabilities

### New Capabilities

- **`rbac-role-catalogue`**: Managed catalog of roles. Each tenant has its own role instances. Seed initializes the 7 domain roles with their baseline permission sets. ADMIN can create custom roles scoped to their tenant.
- **`rbac-permission-catalogue`**: Managed catalog of atomic permissions expressed as `modulo:accion`. Permissions are tenant-scoped. Seed initializes the full permission set from the matrix.
- **`rbac-permission-resolution`**: Server-side resolution of effective permissions per user per request. Takes the user's roles (from DB), unions the permissions, applies tenant scope and assignment validity window. Returns the set of `modulo:accion` strings the user can exercise.
- **`rbac-require-permission-guard`**: `require_permission(permission: str)` FastAPI dependency. Reads the current user from the request state (set by `get_current_user`), resolves effective permissions, checks for the required permission. Missing → 403. Used on every protected endpoint.
- **`rbac-admin-catalog-api`**: Admin-only REST endpoints for managing the role and permission catalogs: `GET /api/admin/roles`, `POST /api/admin/roles`, `GET /api/admin/permisos`, `POST /api/admin/permisos`, `POST /api/admin/roles/{rol_id}/permisos/{permiso_id}` (attach), `DELETE /api/admin/roles/{rol_id}/permisos/{permiso_id}` (detach).

### Modified Capabilities

- **`auth-jwt-2fa`**: No requirement changes. The auth capability's `get_current_user` is extended to expose the user record that feeds the permission resolver. The resolver wires into `get_current_user`'s output, does not change its contract.

---

## Impact

| Area | Impact |
|------|--------|
| **Auth** | `get_current_user` output gains a `permissions: set[str]` field (or a method `.has_permission(p)`) — non-breaking extension |
| **Every backend endpoint** | Every route handler from C-04 onward must declare `require_permission("modulo:accion")` or it is inaccessible |
| **C-05 audit-log** | Depends on `require_permission` existing to guard audit endpoints |
| **C-06 estructura-academica** | Depends on RBAC to protect admin endpoints |
| **C-21 frontend-shell** | Depends on `require_permission` for route guards |
| **Database** | New migration 002: 3 tables + indexes + seed |
| **Tests** | New integration tests: 403 without permission, 200 with permission, role union, `(propio)` scoping, catalog CRUD |

---

## Out of Scope

- Impersonation (`impersonacion:usar`) — owned by C-05 (audit-log).
- Assignment validity window enforcement — owned by C-07 (usuarios-y-asignaciones). C-04 seeds the matrix; the temporal validity logic comes later.
- Roles in the JWT — rejected: forces re-login on role changes, hostile to COORDINADOR setup workflow.
- Hardcoded permission matrix — rejected: must be data (catalog), not code.