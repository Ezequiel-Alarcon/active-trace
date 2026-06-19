## MODIFIED Requirements

### Requirement: PermissionResolver.resolve() SHALL filter by user identity and temporal validity

**Change**: The current `resolve(tenant_id, role_names)` method performs a raw query returning all role-permission mappings without scoping to the requesting user. It MUST be changed to `resolve(tenant_id, user_id)` and perform an inner join through `AsignacionRole` / `Asignacion`, filtering by `user_id`, temporal validity (`desde <= now <= hasta`), and excluding soft-deleted rows (`deleted_at IS NULL`).

The system SHALL compute a user's effective permissions as the set union of all permissions granted by all roles assigned to that user within the tenant, considering only active assignments (within the `desde`/`hasta` window).

#### Scenario: Resolved permissions are scoped to the requesting user

- **WHEN** `PermissionResolver.resolve(tenant_id=T1, user_id=U1)` is called
- **THEN** the query joins through `Asignacion → AsignacionRole → Rol → RolPermiso → Permiso`
- **AND** filters by `Asignacion.user_id = U1`
- **AND** filters by `Asignacion.deleted_at IS NULL`
- **AND** filters by `Asignacion.desde <= now() AND (Asignacion.hasta IS NULL OR Asignacion.hasta >= now())`
- **AND** returns only the permissions from roles whose assignments are active

#### Scenario: Inactive assignments are excluded from resolution

- **WHEN** user U1 has two assignments to role PROFESOR: one active and one with `hasta < now()`
- **THEN** only the active assignment's permissions are included in the resolved set

#### Scenario: Soft-deleted assignments are excluded

- **WHEN** user U1's only assignment to role COORDINADOR has `deleted_at IS NOT NULL`
- **THEN** COORDINADOR's permissions are NOT included in the resolved set
