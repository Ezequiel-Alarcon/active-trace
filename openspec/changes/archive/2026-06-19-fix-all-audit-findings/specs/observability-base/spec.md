## MODIFIED Requirements

### Requirement: audit_emit() SHALL write to the AuditLog table via AuditLogRepository

**Change**: The current `audit_emit()` function in `app/core/audit.py` writes events to `logger.warning(...)`. This is a temporary seam from C-02. The function MUST be changed to call `AuditLogRepository.create(session, ...)` to persist audit events to the `AuditLog` database table.

The function SHALL accept an `AsyncSession` as a required parameter. Callers MUST pass an active DB session. If no session is available (e.g., background task context), the function MAY fall back to logging the event to the structured JSON logger.

#### Scenario: audit_emit persists an event to the AuditLog table

- **WHEN** `audit_emit(session, action="AUTH_LOGIN_OK", user_id=U1, tenant_id=T1)` is called
- **THEN** a new row is created in the `AuditLog` table
- **AND** the row contains `action = "AUTH_LOGIN_OK"`, `user_id = U1`, `tenant_id = T1`
- **AND** no audit event is lost on application restart

#### Scenario: All existing callers pass a DB session

- **WHEN** `audit_emit` is called from any router, service, or repository
- **THEN** an active `AsyncSession` is available and passed as the first argument
- **AND** the audit event is written to the database, not to a logger
