# rbac-permission-catalogue Specification

## MODIFIED Requirements

### Requirement: Permissions are seeded on migration

The system SHALL seed all permissions defined in the capability matrix. Migration 018 SHALL ensure `avisos:publicar` and `avisos:confirmar` permissions exist in the global tenant and are assigned to the correct roles (`avisos:publicar` → COORDINADOR, ADMIN; `avisos:confirmar` → all roles), if they were not already seeded by migration 002.

**Reason**: C-15 introduces the avisos module. These permissions must exist for `require_permission("avisos:publicar")` and `require_permission("avisos:confirmar")` guards to function. Migration 018 adds them via `ON CONFLICT DO NOTHING` to handle both fresh and existing installations.

#### Scenario: Seed creates avisos permissions if missing
- **WHEN** migration 018 runs and `avisos:publicar` or `avisos:confirmar` do not exist in the global tenant
- **THEN** the migration inserts them into the `permiso` table and assigns them to the correct roles in `rol_permiso`

#### Scenario: Seed does not duplicate existing permissions
- **WHEN** migration 018 runs and `avisos:publicar` already exists (e.g., from migration 002)
- **THEN** the migration does not create a duplicate (uses `ON CONFLICT DO NOTHING`)
