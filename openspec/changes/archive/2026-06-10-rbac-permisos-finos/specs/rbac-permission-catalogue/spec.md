# Capability: `rbac-permission-catalogue`

> Defines the managed catalog of atomic permissions expressed as `modulo:accion`. Permissions are tenant-scoped and administrable.

## ADDED Requirements

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

Migration 002 SHALL insert the full set of permissions defined in the capability matrix (§3.3 of `knowledge-base/03_actores_y_roles.md`). The seed includes approximately 20 permissions covering all functional areas.

#### Scenario: Seed creates all matrix permissions

- **WHEN** migration 002 runs for a tenant
- **THEN** the `permiso` table contains at least these permissions:
  - `academico:ver_estado_propio`, `evaluaciones:reservar`, `avisos:confirmar`
  - `calificaciones:importar`, `calificaciones:ver`
  - `atrasados:ver`, `entregas:ver_sin_corregir`
  - `comunicacion:enviar`, `comunicacion:aprobar`
  - `encuentros:gestionar`, `encuentros:registrar_guardia`
  - `tareas:gestionar`, `avisos:publicar`
  - `equipos:asignar`, `estructura:gestionar`
  - `usuarios:gestionar`, `auditoria:ver`, `impersonacion:usar`
  - `finanzas:operar_grilla`, `finanzas:cerrar_liquidacion`, `finanzas:gestionar_facturas`
  - `tenant:configurar`, `roles:gestionar`

### Requirement: Permission supports soft delete

A permission record MUST NOT be physically deleted; instead `deleted_at` is set. Soft-deleted permissions are excluded from normal queries.

#### Scenario: Deleting a permission soft-deletes it

- **WHEN** admin calls `DELETE /api/admin/permisos/{permiso_id}`
- **THEN** the permission's `deleted_at` column is set to the current timestamp
- **AND** subsequent queries do not include that permission