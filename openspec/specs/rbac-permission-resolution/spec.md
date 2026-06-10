# rbac-permission-resolution Specification

## Purpose
TBD - created by archiving change rbac-permisos-finos. Update Purpose after archive.
## Requirements
### Requirement: System SHALL compute effective permissions as the union of all role permissions

The system SHALL compute a user's effective permissions as the set union of all permissions granted by all roles assigned to that user within the tenant.

#### Scenario: User with single role gets that role's permissions

- **WHEN** user has role PROFESOR (which grants `calificaciones:importar`, `atrasados:ver`, `encuentros:gestionar`)
- **AND** the resolver is called for this user in tenant A
- **THEN** the resolved set is exactly `{"calificaciones:importar", "atrasados:ver", "encuentros:gestionar"}`

#### Scenario: User with multiple roles gets union of all permissions

- **WHEN** user has role PROFESOR AND COORDINADOR
- **AND** PROFESOR grants `calificaciones:importar`
- **AND** COORDINADOR grants `calificaciones:importar`, `equipos:asignar`, `avisos:publicar`
- **THEN** the resolved set is `{"calificaciones:importar", "equipos:asignar", "avisos:publicar"}` (union, no duplicates)

### Requirement: System SHALL resolve permissions only from the user's tenant scope

The system SHALL resolve permissions only from roles and permissions belonging to the user's tenant. Cross-tenant permission leakage is impossible.

#### Scenario: Cross-tenant roles are not included in resolution

- **WHEN** user in tenant A has role PROFESOR in tenant A
- **AND** the same user has role ADMIN in tenant B (different tenant)
- **THEN** resolution for tenant A's session returns only permissions from tenant A's PROFESOR role
- **AND** permissions from tenant B's ADMIN role are not included

### Requirement: System SHALL cache permission resolution per request

The system SHALL cache the computed permission set for the lifetime of a single request.

#### Scenario: Second call within same request returns cached permissions

- **WHEN** resolver is called for user U in tenant T for the first time in request R
- **THEN** a DB query is executed to fetch roles and permissions
- **AND** the result is cached
- **WHEN** resolver is called again for user U in tenant T within request R
- **THEN** no DB query is executed
- **AND** the cached set is returned

### Requirement: System SHALL exclude soft-deleted roles from permission resolution

The system SHALL exclude soft-deleted roles from permission resolution.

#### Scenario: Soft-deleted role's permissions are not resolved

- **WHEN** user has role PROFESOR (not deleted) granting `calificaciones:importar`
- **AND** user also has role CUSTOM_ROLE (soft-deleted) granting `finanzas:cerrar_liquidacion`
- **THEN** the resolved set contains `calificaciones:importar` but NOT `finanzas:cerrar_liquidacion`

### Requirement: System SHALL resolve roles from the database, not from JWT claims

The system SHALL resolve roles from the database. The JWT carries only `sub` (user_id), `tid` (tenant_id), and `sid` (session_id).

#### Scenario: Role change takes effect on next request

- **WHEN** admin assigns role ADMIN to user U in tenant T
- **AND** user U already has an active session (JWT)
- **THEN** user U's next request (with same JWT) receives the new ADMIN permissions
- **AND** no re-login is required

### Requirement: Resolution query SHALL be deterministic and performant

The resolution query SHALL be deterministic and performant, using a single optimized query.

#### Scenario: Resolution query uses indexes

- **WHEN** the resolver executes the permission resolution query
- **THEN** PostgreSQL uses `ix_rol_permiso_tenant_rol`, `ix_rol_tenant_nombre`, and `ix_permiso_tenant_modulo_accion` indexes
- **AND** the query plan shows no sequential scans on large tables

