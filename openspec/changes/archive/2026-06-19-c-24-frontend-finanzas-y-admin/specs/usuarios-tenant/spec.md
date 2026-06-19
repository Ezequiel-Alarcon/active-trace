# usuarios-tenant Specification

## ADDED Requirements

### Requirement: Listado de usuarios del tenant
The system SHALL display a list of users in the current tenant, with search and filter capabilities.

#### Scenario: Shows user list with search
- **WHEN** a user with `usuarios:gestionar` navigates to `/admin/usuarios`
- **THEN** the system shows a FilterBar with search input (by nombre/apellidos)
- **AND** calls `GET /api/admin/usuarios?busqueda=<text>`
- **AND** shows a DataTable with columns: nombre, apellidos, email, roles, estado (StatusBadge: Activo/Inactivo), acciones

#### Scenario: Empty list shows EmptyState
- **WHEN** no users match the search
- **THEN** the system shows EmptyState with "No se encontraron usuarios"

### Requirement: Crear y editar usuarios
The system SHALL allow creating and editing tenant users with role assignment.

#### Scenario: Create user form
- **WHEN** the user clicks "Agregar usuario"
- **THEN** a modal form opens with fields: nombre, apellidos, email, dni, cuil, cbu, alias_cbu, banco, regional, roles (multi-select)
- **WHEN** submitted, the system calls `POST /api/admin/usuarios`
- **AND** on success, the table refreshes

#### Scenario: Edit user form
- **WHEN** the user clicks "Editar"
- **THEN** a modal opens pre-filled with current data
- **WHEN** submitted, the system calls `PATCH /api/admin/usuarios/{id}`
- **AND** the table row updates

### Requirement: Soft-delete usuario
The system SHALL allow soft-deleting a user.

#### Scenario: Delete user with confirmation
- **WHEN** the user clicks "Eliminar" on a row
- **THEN** a confirmation dialog shows "¿Eliminar usuario {nombre}?"
- **WHEN** confirmed, the system calls `DELETE /api/admin/usuarios/{id}`
- **AND** the row is removed from the table
