# liquidaciones-grilla-salarial Specification

## ADDED Requirements

### Requirement: ABM SalarioBase por rol con vigencia
The system SHALL allow managing SalarioBase records: importe by role (PROFESOR/TUTOR/NEXO/COORDINADOR) with effective date range.

#### Scenario: Lists SalarioBase records
- **WHEN** a user with `liquidaciones:configurar-salarios` navigates to `/admin/liquidaciones/grilla`
- **THEN** the system calls `GET /api/liquidaciones/salarios-base`
- **AND** shows a DataTable with columns: rol, importe, vigencia_desde, vigencia_hasta, acciones (editar/eliminar)

#### Scenario: Creates new SalarioBase
- **WHEN** the user clicks "Agregar Salario Base"
- **THEN** a modal form opens with fields: rol (select), importe (number), vigencia_desde (date), vigencia_hasta (date, optional)
- **WHEN** the user submits valid data, the system calls `POST /api/liquidaciones/salarios-base`
- **AND** on success, the modal closes, the table refreshes, and a success toast shows

#### Scenario: Edits existing SalarioBase
- **WHEN** the user clicks "Editar" on a row
- **THEN** a modal form opens pre-filled with the current values
- **WHEN** the user modifies and submits, the system calls `PATCH /api/liquidaciones/salarios-base/{id}`
- **AND** on success, the table row updates

#### Scenario: Deletes SalarioBase (soft)
- **WHEN** the user clicks "Eliminar" on a row
- **THEN** a confirmation dialog appears
- **WHEN** confirmed, the system calls `DELETE /api/liquidaciones/salarios-base/{id}`
- **AND** the row is removed from the table

### Requirement: ABM SalarioPlus por clave y rol con vigencia
The system SHALL allow managing SalarioPlus records: additional amounts identified by key/group, role, and description with effective date range.

#### Scenario: Lists SalarioPlus records
- **WHEN** the user switches to "Plus" tab
- **THEN** the system calls `GET /api/liquidaciones/salarios-plus`
- **AND** shows a DataTable with columns: clave, rol, descripcion, importe, vigencia_desde, vigencia_hasta, acciones

#### Scenario: CRUD operations for SalarioPlus
- **WHEN** the user creates/edits/deletes a SalarioPlus record
- **THEN** the same modal + confirmation flow as SalarioBase applies
- **AND** endpoints are `POST /api/liquidaciones/salarios-plus`, `PATCH /api/liquidaciones/salarios-plus/{id}`, `DELETE /api/liquidaciones/salarios-plus/{id}`
