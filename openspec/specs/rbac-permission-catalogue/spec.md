# rbac-permission-catalogue Specification

## Purpose
TBD - created by archiving change rbac-permisos-finos. Update Purpose after archive.
## Requirements
### Requirement: Permission catalog is tenant-scoped

The system SHALL store each permission with a `tenant_id` foreign key. A permission MUST NOT be accessible to users outside its tenant. All repository queries for permissions MUST filter by `tenant_id`.

#### Scenario: Permission from Tenant A not visible in Tenant B

- **WHEN** admin from tenant A creates permission `calificaciones:importar`
- **AND** admin from tenant B queries `GET /api/admin/permisos`
- **THEN** `calificaciones:importar` is not present in tenant B's catalog

### Requirement: Permission is uniquely identified by tenant + modulo + accion

The combination `(tenant_id, modulo, accion)` MUST be unique. No two permissions with the same modulo and accion can exist within the same tenant.

#### Scenario: Duplicate permission within tenant is rejected

- **WHEN** admin creates permission `calificaciones:importar` in tenant A
- **AND** admin attempts to create another permission with `modulo = "calificaciones"` and `accion = "importar"` in tenant A
- **THEN** the system returns `409 Conflict` with `{"detail": "Ya existe ese permiso en este tenant"}`

### Requirement: Permission formato `modulo:accion`

Every permission in the system SHALL be expressed as `modulo:accion` where `modulo` is the functional area (e.g., `calificaciones`, `equipos`, `auditoria`) and `accion` is the specific action (e.g., `importar`, `ver`, `aprobar`). The full permission string (e.g., `"calificaciones:importar"`) is stored as the canonical identifier used in `require_permission` checks.

#### Scenario: Permission stores canonical modulo:accion string

- **WHEN** admin creates permission with `modulo = "comunicacion"` and `accion = "aprobar"`
- **THEN** the stored permission has `modulo = "comunicacion"`, `accion = "aprobar"`
- **AND** the canonical string `"comunicacion:aprobar"` is used in permission resolution

### Requirement: Permissions are seeded on migration

The system SHALL seed all permissions defined in the capability matrix. Migration 018 SHALL ensure `avisos:publicar` and `avisos:confirmar` permissions exist in the global tenant and are assigned to the correct roles (`avisos:publicar` → COORDINADOR, ADMIN; `avisos:confirmar` → all roles), if they were not already seeded by migration 002.

**Reason**: C-15 introduces the avisos module. These permissions must exist for `require_permission("avisos:publicar")` and `require_permission("avisos:confirmar")` guards to function. Migration 018 adds them via `ON CONFLICT DO NOTHING` to handle both fresh and existing installations.

#### Scenario: Seed creates avisos permissions if missing
- **WHEN** migration 018 runs and `avisos:publicar` or `avisos:confirmar` do not exist in the global tenant
- **THEN** the migration inserts them into the `permiso` table and assigns them to the correct roles in `rol_permiso`

#### Scenario: Seed does not duplicate existing permissions
- **WHEN** migration 018 runs and `avisos:publicar` already exists (e.g., from migration 002)
- **THEN** the migration does not create a duplicate (uses `ON CONFLICT DO NOTHING`)

### Requirement: Permission supports soft delete

A permission record MUST NOT be physically deleted; instead `deleted_at` is set. Soft-deleted permissions are excluded from normal queries.

#### Scenario: Deleting a permission soft-deletes it

- **WHEN** admin calls `DELETE /api/admin/permisos/{permiso_id}`
- **THEN** the permission's `deleted_at` column is set to the current timestamp
- **AND** subsequent queries do not include that permission

