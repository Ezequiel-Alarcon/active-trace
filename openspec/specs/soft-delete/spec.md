## ADDED Requirements

### Requirement: Soft delete is the only supported delete operation

The system MUST NOT support hard delete on any domain table inheriting the `TenantScopedMixin`. A delete operation on a domain row MUST set `deleted_at` to the current server time and leave the row in the database. A hard delete MUST be reachable only through a method prefixed `unsafe_` on the repository base, and that call MUST emit an audit event with action `ROW_HARD_DELETE`.

#### Scenario: Calling `soft_delete` sets `deleted_at` and keeps the row

- **WHEN** a repository's `soft_delete(obj)` is called
- **THEN** the row's `deleted_at` is set to the current server time, the row is not physically removed, and subsequent `list`/`get` calls that filter by `deleted_at IS NULL` do not return it

#### Scenario: `restore` clears `deleted_at` and brings the row back

- **WHEN** a repository's `restore(obj)` is called on a soft-deleted row
- **THEN** the row's `deleted_at` is set to `null` and the row becomes visible again to `list`/`get` that filter by `deleted_at IS NULL`

#### Scenario: `list` and `count` ignore soft-deleted rows by default

- **WHEN** a repository's `list` or `count` is called
- **THEN** the result set and the counter exclude rows with `deleted_at IS NOT NULL`

#### Scenario: `unsafe_list_all` includes soft-deleted rows and emits audit

- **WHEN** a repository's `unsafe_list_all` is called
- **THEN** the result set includes rows with `deleted_at IS NOT NULL` and the call emits an audit event with action `TENANT_CROSS_QUERY` (or `ROW_INCLUDE_DELETED` for non-cross-tenant variants) via the `audit_emit` seam

### Requirement: Soft delete does not break foreign-key integrity

Soft-deleting a parent row MUST NOT cascade soft-delete to child rows. A child row referencing a soft-deleted parent MUST remain in its current `deleted_at` state; if the application logic requires hiding the child too, it MUST be done explicitly by the service. Hard-deleting a parent row MUST be rejected by the database (`ON DELETE RESTRICT` on tenant FK; child tables introduced in later changes MUST declare the appropriate `ON DELETE` policy in their own migrations).

#### Scenario: Soft-deleting a tenant does not cascade to its children

- **WHEN** a `tenant` row is soft-deleted
- **THEN** rows in child tables that reference that tenant keep their current `deleted_at` value and are not automatically soft-deleted

#### Scenario: Hard-deleting a tenant that has children is rejected

- **WHEN** a hard delete is attempted on a `tenant` row that has at least one referencing row in any child table
- **THEN** the database raises a foreign-key violation and the tenant is not removed

### Requirement: Soft delete is observable from the audit log

Every `soft_delete` and every `restore` MUST emit an audit event. The event MUST include the entity name, the row `id`, the `tenant_id`, and the timestamp. In C-02 the emission goes through the `audit_emit` seam; C-05 will wire the seam to the persistent `AuditLog` table. Until C-05 lands, the seam MUST at minimum log to a structured logger with action codes `ROW_SOFT_DELETE` and `ROW_RESTORE`.

#### Scenario: `soft_delete` emits an audit event

- **WHEN** a repository's `soft_delete` is called
- **THEN** an audit event is emitted with action `ROW_SOFT_DELETE`, the entity name, the row `id`, and the current `tenant_id`

#### Scenario: `restore` emits an audit event

- **WHEN** a repository's `restore` is called
- **THEN** an audit event is emitted with action `ROW_RESTORE`, the entity name, the row `id`, and the current `tenant_id`

### Requirement: LiquidacionRepository SHALL use soft delete instead of hard delete

`LiquidacionRepository` SHALL perform a soft delete via `update(Liquidacion).where(...).values(deleted_at=func.now(), deleted_by=<user_id>)` instead of a hard delete.

#### Scenario: Deleting a liquidacion sets deleted_at instead of removing the row

- **WHEN** `LiquidacionRepository.delete(session, liquidacion_id=L1)` is called
- **THEN** the row with id=L1 has `deleted_at` set to the current server time
- **AND** the row is NOT physically removed from the database
- **AND** subsequent `list`/`get` calls (which filter by `deleted_at IS NULL`) do not return it

### Requirement: AuditLogRepository deleted_at SHALL match the standard pattern

The `AuditLogRepository` SHALL use `deleted_at` as the soft-delete column name matching the base repository pattern. If the column uses a different name, a migration MUST rename it.

#### Scenario: AuditLogRepository uses standard deleted_at column

- **WHEN** inspecting the `AuditLog` model and its repository
- **THEN** the soft-delete column is named `deleted_at` matching the base repository pattern
- **AND** the repository's `list`/`get` methods filter by `deleted_at IS NULL`
