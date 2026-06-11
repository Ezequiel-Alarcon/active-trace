# Capability: `audit-log-decorator`

> `@audit("ACCION_CODIGO")` decorator on service methods automatically captures context (actor, tenant, timestamp, IP, user agent, rows affected) and writes the AuditLog entry.

## ADDED Requirements

### Requirement: System SHALL provide an @audit decorator for service methods

The system SHALL provide a `@audit(action_code: str)` decorator that can be applied to any service method. When called, the decorator SHALL automatically capture the current request context and write an AuditLog entry.

#### Scenario: @audit decorator creates an audit entry with correct context

- **WHEN** a service method decorated with `@audit("CALIFICACIONES_IMPORTAR")` is called
- **THEN** an AuditLog entry is created with `accion = "CALIFICACIONES_IMPORTAR"`
- **AND** `actor_id` is taken from `request.state.current_user.id`
- **AND** `tenant_id` is taken from `request.state.current_user.tenant_id`
- **AND** `fecha_hora` is set to the current server timestamp
- **AND** `ip` is taken from `request.state["ip"]` (set by middleware)
- **AND** `user_agent` is taken from `request.state["user_agent"]`
- **AND** `filas_afectadas` is set to the return value of the decorated method (if applicable)

### Requirement: @audit decorator SHALL NOT block the main execution flow

The AuditLog write SHALL be fire-and-forget: it SHALL NOT raise an exception to the caller if the audit write fails. Audit failures SHALL be logged but SHALL NOT cause the action to fail.

#### Scenario: Audit write failure does not roll back the main action

- **WHEN** a service method decorated with `@audit("CALIFICACIONES_IMPORTAR")` is called
- **AND** the audit log write fails (e.g., DB connection error)
- **THEN** the service method completes successfully
- **AND** the error is logged but not raised to the caller

### Requirement: @audit decorator SHALL record filas_afectadas from method return value

When the decorated method returns an integer, that value SHALL be recorded as `filas_afectadas`. When it returns None or a non-integer, `filas_afectadas` SHALL be set to 0.

#### Scenario: filas_afectadas is recorded from return value

- **WHEN** a service method decorated with `@audit("CALIFICACIONES_IMPORTAR")` returns 42 (count of rows imported)
- **THEN** the AuditLog entry has `filas_afectadas = 42`

### Requirement: @audit decorator SHALL support async service methods

The decorator SHALL work with both sync and async service methods. For async methods, the audit entry is written after the method completes successfully.

#### Scenario: @audit decorator works with async service methods

- **WHEN** an async service method decorated with `@audit("USUARIOS_GESTIONAR")` is called with await
- **THEN** the AuditLog entry is written after the coroutine completes
- **AND** the audit write does not block the response