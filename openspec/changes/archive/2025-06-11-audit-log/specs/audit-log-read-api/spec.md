# Capability: `audit-log-read-api`

> `GET /api/audit/log` — paginated, filterable audit log read API. Requires `auditoria:ver` permission. ADMIN sees all tenants; COORDINADOR sees only their own tenant.

## ADDED Requirements

### Requirement: System SHALL provide GET /api/audit/log endpoint

The system SHALL provide a `GET /api/audit/log` endpoint that returns a paginated list of AuditLog entries. The endpoint requires `auditoria:ver` permission.

#### Scenario: Authenticated user with auditoria:ver can list audit logs

- **WHEN** user with `auditoria:ver` calls `GET /api/audit/log`
- **THEN** response is `200 OK` with JSON array of AuditLog entries
- **AND** entries are ordered by `fecha_hora DESC`

### Requirement: Audit log endpoint SHALL support pagination

The system SHALL support `page` (default 1) and `page_size` (default 50, max 200) query parameters. Response SHALL include `total`, `page`, `page_size`, and `items`.

#### Scenario: Pagination returns correct page

- **WHEN** user calls `GET /api/audit/log?page=2&page_size=20`
- **THEN** response contains at most 20 items
- **AND** response includes `{"total": N, "page": 2, "page_size": 20, "items": [...]}`

### Requirement: Audit log endpoint SHALL support filtering by actor_id

The system SHALL support `actor` query parameter to filter by `actor_id`.

#### Scenario: Filter by actor returns only matching entries

- **WHEN** user calls `GET /api/audit/log?actor=UUID_OF_ACTOR`
- **THEN** all returned entries have `actor_id = UUID_OF_ACTOR`

### Requirement: Audit log endpoint SHALL support filtering by accion

The system SHALL support `accion` query parameter to filter by action code.

#### Scenario: Filter by accion returns only matching entries

- **WHEN** user calls `GET /api/audit/log?accion=CALIFICACIONES_IMPORTAR`
- **THEN** all returned entries have `accion = "CALIFICACIONES_IMPORTAR"`

### Requirement: Audit log endpoint SHALL support filtering by date range

The system SHALL support `from` and `to` query parameters (ISO 8601 timestamps) to filter by `fecha_hora`.

#### Scenario: Filter by date range returns entries within range

- **WHEN** user calls `GET /api/audit/log?from=2026-01-01T00:00:00Z&to=2026-01-31T23:59:59Z`
- **THEN** all returned entries have `fecha_hora` between the specified range

### Requirement: ADMIN can see all tenants' audit logs; COORDINADOR sees only their own tenant

The system SHALL enforce tenant scoping based on role. ADMIN (with `auditoria:ver`) can query across all tenants by passing `?all_tenants=true`. COORDINADOR always sees only their own tenant's logs.

#### Scenario: ADMIN can query all tenants' logs

- **WHEN** ADMIN calls `GET /api/audit/log?all_tenants=true`
- **THEN** returned entries include logs from all tenants
- **AND** ADMIN's own tenant filter is not applied

#### Scenario: COORDINADOR cannot see other tenants' logs

- **WHEN** COORDINADOR calls `GET /api/audit/log`
- **THEN** all returned entries have `tenant_id = COORDINADOR's tenant_id`
- **AND** entries from other tenants are not included

### Requirement: User without auditoria:ver cannot access audit logs

The system SHALL return `403 Forbidden` for users without `auditoria:ver` permission.

#### Scenario: User without auditoria:ver gets 403

- **WHEN** user WITHOUT `auditoria:ver` calls `GET /api/audit/log`
- **THEN** response is `403 Forbidden` with `{"detail": "No tiene el permiso: auditoria:ver"}`