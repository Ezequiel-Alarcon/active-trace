# Capability: `audit-log-append-only`

> The `audit_log` table is append-only. No UPDATE or DELETE path exists at any layer. All significant actions generate an AuditLog entry.

## ADDED Requirements

### Requirement: System SHALL create an AuditLog entry for every significant action

The system SHALL record every significant action in the `audit_log` table with the following fields: `id` (UUID), `tenant_id` (UUID), `fecha_hora` (TIMESTAMPTZ, server-set), `actor_id` (UUID), `impersonado_id` (UUID, nullable), `materia_id` (UUID, nullable), `accion` (VARCHAR(64)), `detalle` (JSONB, nullable), `filas_afectadas` (INTEGER, default 0), `ip` (VARCHAR(64)), `user_agent` (VARCHAR(512)).

#### Scenario: Audit entry is created for a significant action

- **WHEN** a user performs a significant action (e.g., imports calificaciones)
- **THEN** an AuditLog entry is created with the correct actor_id, tenant_id, accion, fecha_hora, ip, and user_agent
- **AND** the entry is persisted to the database

### Requirement: System SHALL NOT allow UPDATE on audit_log entries

The system SHALL NOT provide any method to update an AuditLog entry. At the repository layer, only `create` exists. At the DB level, no UPDATE path is used by the application.

#### Scenario: Attempting to update an audit log entry raises an error

- **WHEN** any code attempts to call `AuditLogRepository.update()` on an audit_log entry
- **THEN** the method does not exist and an AttributeError is raised
- **OR** the repository explicitly raises NotImplementedError

### Requirement: System SHALL NOT allow DELETE on audit_log entries

The system SHALL NOT provide any method to delete an AuditLog entry. The repository has no `delete` or `soft_delete` method for AuditLog.

#### Scenario: Attempting to delete an audit log entry raises an error

- **WHEN** any code attempts to call `AuditLogRepository.delete()` on an audit_log entry
- **THEN** the method does not exist and an AttributeError is raised
- **OR** the repository explicitly raises NotImplementedError

### Requirement: System SHALL scope all audit log entries to the current tenant

The system SHALL set `tenant_id` on every AuditLog entry from the current request context. Cross-tenant audit visibility is controlled by role (`auditoria:ver`).

#### Scenario: Audit entry inherits tenant from request context

- **WHEN** a user in tenant A performs an audited action
- **THEN** the resulting AuditLog entry has `tenant_id = tenant A's id`
- **AND** the entry is not visible in tenant B's audit queries