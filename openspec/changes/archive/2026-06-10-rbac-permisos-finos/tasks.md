# Tasks: C-04 — RBAC Permisos Finos

> Strict TDD: test fails → code minimum → triangulate → refactor.
> No DB mocks. Use real DB (container or ephemeral).

---

## 1. Migration 002: rol, permiso, rol_permiso + seed

- [x] 1.1 Generate Alembic migration `004_rbac_tables.py`
- [x] 1.2 Create `rol` table: `id` UUID PK, `tenant_id` UUID FK→tenant, `nombre` VARCHAR(64) NOT NULL, `descripcion` VARCHAR(255), `created_at`, `updated_at`, `deleted_at`; UNIQUE(tenant_id, nombre); index on `tenant_id`
- [x] 1.3 Create `permiso` table: `id` UUID PK, `tenant_id` UUID FK→tenant, `modulo` VARCHAR(64) NOT NULL, `accion` VARCHAR(64) NOT NULL, `created_at`, `updated_at`, `deleted_at`; UNIQUE(tenant_id, modulo, accion); index on `tenant_id`
- [x] 1.4 Create `rol_permiso` table: `id` UUID PK, `tenant_id` UUID FK→tenant, `rol_id` UUID FK→rol, `permiso_id` UUID FK→permiso, `created_at`; UNIQUE(tenant_id, rol_id, permiso_id); indexes on `(tenant_id, rol_id)` and `(tenant_id, permiso_id)`
- [x] 1.5 Add seed data: raw SQL `INSERT` for 7 domain roles + ~23 permissions + full `rol_permiso` matrix (ALUMNO×N, TUTOR×N, PROFESOR×N, COORDINADOR×N, NEXO×N, ADMIN×N, FINANZAS×N)
- [x] 1.6 Verify migration: run `alembic upgrade head`, confirm `SELECT COUNT(*) FROM rol` returns 7, `SELECT COUNT(*) FROM permiso` returns ~23, `SELECT COUNT(*) FROM rol_permiso` returns correct matrix count

---

## 2. Domain Models (SQLAlchemy)

- [x] 2.1 Create `app/rbac/models.py` with `Rol`, `Permiso`, `RolPermiso` models
  - `Rol`: `id`, `tenant_id`, `nombre`, `descripcion`, `created_at`, `updated_at`, `deleted_at`
  - `Permiso`: `id`, `tenant_id`, `modulo`, `accion`, `created_at`, `updated_at`, `deleted_at`
  - `RolPermiso`: `id`, `tenant_id`, `rol_id`, `permiso_id`, `created_at`
  - Relationships: `Rol.permisos` (many-to-many via `RolPermiso`), `Permiso.roles` (back-pop)
- [x] 2.2 Register models in `app/models/__init__.py`
- [x] 2.3 Verify models compile and are discoverable by Alembic

---

## 3. Repositories (RBAC)

- [x] 3.1 Create `app/rbac/repositories.py`
  - `RolRepository`: `get_by_tenant`, `get_by_id`, `create`, `update`, `soft_delete`, `get_by_nombre`
  - `PermisoRepository`: `get_by_tenant`, `get_by_id`, `create`, `get_by_modulo_accion`
  - `RolPermisoRepository`: `attach`, `detach`, `get_permisos_by_rol`, `get_roles_by_permiso`
  - All methods filter by `tenant_id` by default (TenantScopedMixin pattern)
- [x] 3.2 Verify: create, list, soft-delete, attach/detach in unit test against real DB

---

## 4. PermissionResolver Service

- [x] 4.1 Create `app/rbac/services.py` with `PermissionResolver`
  - `__init__(db: AsyncSession)` — stores session
  - `resolve(user_id: UUID, tenant_id: UUID) → set[str]` — single query: joins `asignacion → rol → rol_permiso → permiso`, filters by `tenant_id`, excludes `deleted_at`, returns `{f"{p.modulo}:{p.accion}"}`
  - Request-scoped cache: dict keyed by `(user_id, tenant_id)` — cache on instance, not class
- [x] 4.2 Create `app/rbac/__init__.py` exporting `PermissionResolver`
- [x] 4.3 Write unit tests: single role, multiple roles (union), cross-tenant isolation, soft-deleted role excluded, cache hit on second call

---

## 5. `require_permission` Guard

- [x] 5.1 Implement `require_permission(permission: str)` in `app/core/permissions.py`
  - Depends on `get_current_user` from `app.auth.deps`
  - Calls `PermissionResolver.resolve(current_user.id, current_user.tenant_id)`
  - Checks if `permission` in resolved set → 403 if missing
  - Attaches `permissions` to `request.state`
- [x] 5.2 Write integration test: authenticated user without `calificaciones:importar` → 403; with it → 200
- [x] 5.3 Verify: unauthenticated request → 401 before permission check

---

## 6. Wire `permissions` into `get_current_user` (C-03 extension)

- [x] 6.1 Extend `AuthUser` (or the return type of `get_current_user`) to include `permissions: set[str]` field
  - Option: add `.permissions` property that lazily resolves via `PermissionResolver` and caches on the user object
  - Option B (cleaner): have `get_current_user` return a `AuthUserWithPermissions` dataclass that wraps `AuthUser` and adds the resolved permissions
- [x] 6.2 Ensure `request.state.current_user` exposes permissions to downstream handlers
- [x] 6.3 Write test: after calling `get_current_user`, the returned object has `permissions` attribute populated

---

## 7. Admin Catalog API (RBAC endpoints)

- [x] 7.1 Create `app/rbac/router.py` — router `/api/admin` with all catalog endpoints
  - `GET /roles` → `list_roles` (requires `admin:gestionar_roles`)
  - `POST /roles` → `create_role`
  - `GET /roles/{role_id}` → `get_role_detail` (includes permissions)
  - `PATCH /roles/{role_id}` → `update_role`
  - `DELETE /roles/{role_id}` → `soft_delete_role`
  - `GET /permisos` → `list_permisos`
  - `POST /permisos` → `create_permiso`
  - `POST /roles/{rol_id}/permisos/{permiso_id}` → `attach_permiso`
  - `DELETE /roles/{rol_id}/permisos/{permiso_id}` → `detach_permiso`
  - `GET /roles/{rol_id}/permisos` → `list_role_permisos`
- [x] 7.2 All endpoints declare `require_permission("admin:gestionar_roles")` at router level
- [x] 7.3 Register router in `app/main.py` under `/api/admin`
- [x] 7.4 Write integration tests: admin CRUD for roles and permissions, attach/detach, 409 on duplicate, 404 on missing, 403 for non-admin

---

## 8. Public endpoint: `GET /api/permissions/me`

- [x] 8.1 Create `app/rbac/public_router.py` — router `/api/permissions`
  - `GET /me` → `get_my_permissions` (auth required, no specific permission required — any authenticated user can see their own permissions)
- [x] 8.2 Registers in `app/main.py` under `/api/permissions`
- [x] 8.3 Write test: authenticated user gets their effective permission set

---

## 9. Integration Tests — Full RBAC Flow

- [x] 9.1 Test: user without required permission → 403
- [x] 9.2 Test: user with required permission → 200
- [x] 9.3 Test: user with multiple roles → union of permissions
- [x] 9.4 Test: cross-tenant isolation (tenant A user cannot see tenant B roles/permissions)
- [x] 9.5 Test: soft-deleted role does not contribute permissions
- [x] 9.6 Test: admin catalog CRUD — create, list, update, soft-delete roles
- [x] 9.7 Test: attach/detach permission↔role (409 on duplicate attach)
- [x] 9.8 Test: `GET /api/permissions/me` returns correct effective permissions
- [x] 9.9 Run full integration suite → all pass

---

## 10. Verify and Archive

- [x] 10.1 Run `openspec verify` to confirm implementation matches specs
- [x] 10.2 Run full test suite (unit + integration) → ≥80% line coverage, all green
- [x] 10.3 Commit and push C-04 branch
- [x] 10.4 `/opsx:archive rbac-permisos-finos`
- [x] 10.5 Mark `[x]` for C-04 in CHANGES.md