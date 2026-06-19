## MODIFIED Requirements

### Requirement: LiquidacionRepository SHALL use soft delete instead of hard delete

**Change**: `LiquidacionRepository` currently performs a hard delete via `delete(Liquidacion).where(...)`. This MUST be replaced with a soft delete: `update(Liquidacion).where(...).values(deleted_at=func.now(), deleted_by=<user_id>)`.

#### Scenario: Deleting a liquidacion sets deleted_at instead of removing the row

- **WHEN** `LiquidacionRepository.delete(session, liquidacion_id=L1)` is called
- **THEN** the row with id=L1 has `deleted_at` set to the current server time
- **AND** the row is NOT physically removed from the database
- **AND** subsequent `list`/`get` calls (which filter by `deleted_at IS NULL`) do not return it

### Requirement: AuditLogRepository deleted_at SHALL match the standard pattern

**Change**: The `AuditLogRepository` uses a column name that does not match the standard soft-delete pattern. The column name MUST be `deleted_at` (not `deleted_at_audit` or any variant). If the column is wrong, a migration MUST rename it.

#### Scenario: AuditLogRepository uses standard deleted_at column

- **WHEN** inspecting the `AuditLog` model and its repository
- **THEN** the soft-delete column is named `deleted_at` matching the base repository pattern
- **AND** the repository's `list`/`get` methods filter by `deleted_at IS NULL`
