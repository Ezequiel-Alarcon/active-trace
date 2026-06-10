# Capability: `rbac-admin-catalog-api`

> Admin-only REST endpoints for managing the role and permission catalogs. All endpoints require `admin:gestionar_roles` permission.

## ADDED Requirements

### Requirement: System SHALL list all non-soft-deleted roles for the current tenant

The system SHALL return all non-soft-deleted roles for the current tenant, ordered by `nombre` ascending.

#### Scenario: List roles returns tenant-scoped results

- **WHEN** admin calls `GET /api/admin/roles`
- **THEN** response is `200 OK` with JSON array of role objects
- **AND** each role has `id`, `nombre`, `descripcion`, `created_at`, `updated_at`
- **AND** no soft-deleted roles are included

### Requirement: System SHALL create a new role when admin provides valid data

The system SHALL create a new role when admin provides valid data. Requires `admin:gestionar_roles`. Rejects duplicate `nombre` within the same tenant with `409 Conflict`.

#### Scenario: Create role succeeds

- **WHEN** admin calls `POST /api/admin/roles` with `{"nombre": "SUPERVISOR", "descripcion": "Supervisor deArea"}`
- **THEN** response is `201 Created` with the created role object
- **AND** `tenant_id` is set to the current tenant from session

#### Scenario: Create role with duplicate name fails

- **WHEN** admin calls `POST /api/admin/roles` with `{"nombre": "PROFESOR"}` (already exists in tenant)
- **THEN** response is `409 Conflict` with `{"detail": "Ya existe un rol con ese nombre en este tenant"}`

### Requirement: System SHALL return a single role with its attached permissions

The system SHALL return a single role with its attached permissions.

#### Scenario: Get existing role

- **WHEN** admin calls `GET /api/admin/roles/{role_id}` for a valid role
- **THEN** response is `200 OK` with role object including `permisos` array (each with `id`, `modulo`, `accion`)

#### Scenario: Get non-existent role returns 404

- **WHEN** admin calls `GET /api/admin/roles/{unknown_id}`
- **THEN** response is `404 Not Found`

### Requirement: System SHALL update role fields when admin provides valid data

The system SHALL update role fields when admin provides valid data.

#### Scenario: Update role name

- **WHEN** admin calls `PATCH /api/admin/roles/{role_id}` with `{"nombre": "PROFISOR"}`
- **THEN** response is `200 OK` with updated role
- **AND** `updated_at` is refreshed

### Requirement: System SHALL soft-delete a role without physical deletion

The system SHALL soft-delete a role (set `deleted_at`) without physical deletion.

#### Scenario: Delete role soft-deletes

- **WHEN** admin calls `DELETE /api/admin/roles/{role_id}`
- **THEN** response is `204 No Content`
- **AND** `deleted_at` is set on the role
- **AND** subsequent list queries do not return this role

### Requirement: System SHALL list all non-soft-deleted permissions for the tenant

The system SHALL list all non-soft-deleted permissions for the tenant, ordered by `modulo, accion`.

#### Scenario: List permissions returns tenant-scoped results

- **WHEN** admin calls `GET /api/admin/permisos`
- **THEN** response is `200 OK` with JSON array of permission objects
- **AND** each has `id`, `modulo`, `accion`, `created_at`, `updated_at`
- **AND** no soft-deleted permissions are included

### Requirement: System SHALL create a new permission when admin provides valid data

The system SHALL create a new permission when admin provides valid data. Requires `admin:gestionar_roles`. Rejects duplicate `(modulo, accion)` within tenant.

#### Scenario: Create permission succeeds

- **WHEN** admin calls `POST /api/admin/permisos` with `{"modulo": "reportes", "accion": "exportar"}`
- **THEN** response is `201 Created` with the created permission object

#### Scenario: Create duplicate permission fails

- **WHEN** admin calls `POST /api/admin/permisos` with `{"modulo": "calificaciones", "accion": "importar"}` (already exists in tenant)
- **THEN** response is `409 Conflict` with `{"detail": "Ya existe ese permiso en este tenant"}`

### Requirement: System SHALL attach a permission to a role via rol_permiso junction

The system SHALL attach a permission to a role via the `rol_permiso` junction table.

#### Scenario: Attach permission to role

- **WHEN** admin calls `POST /api/admin/roles/{rol_id}/permisos/{permiso_id}`
- **AND** both role and permission belong to the current tenant
- **THEN** response is `201 Created` with the `rol_permiso` junction record
- **AND** subsequent role detail queries include this permission

#### Scenario: Attach already-attached permission returns 409

- **WHEN** permission P is already attached to role R
- **AND** admin calls `POST /api/admin/roles/{rol_id}/permisos/{permiso_id}` again
- **THEN** response is `409 Conflict` with `{"detail": "El permiso ya esta asociado a este rol"}`

### Requirement: System SHALL detach a permission from a role by removing the junction record

The system SHALL detach a permission from a role by removing the `rol_permiso` junction record.

#### Scenario: Detach permission from role

- **WHEN** admin calls `DELETE /api/admin/roles/{rol_id}/permisos/{permiso_id}`
- **THEN** response is `204 No Content`
- **AND** the `rol_permiso` record is deleted (hard delete — attachment is not audit-logged)

### Requirement: System SHALL deny access to admin catalog endpoints for users without admin:gestionar_roles

The system SHALL deny access to admin catalog endpoints for users without `admin:gestionar_roles` permission.

#### Scenario: Non-admin user cannot list roles

- **WHEN** user WITHOUT `admin:gestionar_roles` calls `GET /api/admin/roles`
- **THEN** response is `403 Forbidden` with `{"detail": "No tiene el permiso: admin:gestionar_roles"}`

#### Scenario: Non-admin user cannot create permission

- **WHEN** user WITHOUT `admin:gestionar_roles` calls `POST /api/admin/permisos`
- **THEN** response is `403 Forbidden`