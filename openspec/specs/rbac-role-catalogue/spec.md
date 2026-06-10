# rbac-role-catalogue Specification

## Purpose
TBD - created by archiving change rbac-permisos-finos. Update Purpose after archive.
## Requirements
### Requirement: Role catalog is tenant-scoped

The system SHALL store each role with a `tenant_id` foreign key. A role MUST NOT be accessible to users outside its tenant. All repository queries for roles MUST filter by `tenant_id`.

#### Scenario: Admin in Tenant A cannot see Tenant B's roles

- **WHEN** admin from tenant A queries `GET /api/admin/roles`
- **THEN** the response contains only roles where `tenant_id = tenant A's id`
- **AND** roles belonging to tenant B are not present in the response

#### Scenario: Role name is unique per tenant

- **WHEN** admin creates a role with name `"PROFESOR"` in tenant A
- **AND** admin creates a role with name `"PROFESOR"` in tenant B (same name, different tenant)
- **THEN** both creations succeed
- **AND** each role is isolated to its tenant

#### Scenario: Duplicate role name within same tenant is rejected

- **WHEN** admin creates a role with name `"PROFESOR"` in tenant A
- **AND** admin attempts to create another role with name `"PROFESOR"` in tenant A
- **THEN** the system returns `409 Conflict` with `{"detail": "Ya existe un rol con ese nombre en este tenant"}`

### Requirement: Domain roles are seeded on migration

When migration 002 runs (`alembic upgrade head`), the system SHALL insert the 7 domain roles (ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS) as seed data under each tenant's context.

The seed is idempotent: running the migration multiple times produces the same result (roles exist, no duplicates).

#### Scenario: Seed creates all 7 domain roles

- **WHEN** migration 002 runs for a tenant
- **THEN** the `rol` table contains exactly 7 rows with names: ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS
- **AND** each has `tenant_id` set to the target tenant

### Requirement: Roles support soft delete

A role record MUST NOT be physically deleted (`DELETE`); instead `deleted_at` is set to the current timestamp. Soft-deleted roles are excluded from all normal queries but preserved for audit.

#### Scenario: Deleting a role soft-deletes it

- **WHEN** admin calls `DELETE /api/admin/roles/{role_id}`
- **THEN** the role's `deleted_at` column is set to the current timestamp
- **AND** subsequent `GET /api/admin/roles` does not include that role
- **AND** `SELECT * FROM rol WHERE id = {role_id}` still returns the row with `deleted_at` set

### Requirement: Role has standard audit fields

Every role record MUST have `id` (UUID, PK), `tenant_id` (UUID, FK), `nombre` (VARCHAR(64), NOT NULL), `descripcion` (VARCHAR(255)), `created_at`, `updated_at`, `deleted_at`.

#### Scenario: New role has all required fields

- **WHEN** admin creates a role with `nombre = "PROFESOR"` and `descripcion = "Docente a cargo"`
- **THEN** the system returns the created role with a generated `id`, `tenant_id` (from session), `created_at`, `updated_at`, and `deleted_at = NULL`

