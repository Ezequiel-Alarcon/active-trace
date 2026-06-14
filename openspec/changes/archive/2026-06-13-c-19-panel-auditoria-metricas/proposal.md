## Why

The audit system (C-05) already captures every action in the append-only `audit_log` table, but there is no query layer that exposes aggregated metrics or interactive dashboards. Coordinators and admins need visibility into system usage trends, communication delivery status, and per-docente activity without digging through raw log rows. This change builds a read-only metrics and panel layer on top of the existing audit log.

## What Changes

- New service methods in `AuditLogService` for aggregation queries:
  - actions per day (time series, optionally filtered by user)
  - communication status counts grouped by docente and materia
  - interactions summary by docente and materia (action type counts)
  - last actions log with configurable limit (default 200)
- New router endpoints under `/api/audit/` for each metric query
- New Pydantic response schemas for metric payloads
- Scope filtering: COORDINADOR `(propio)` sees only data for docentes in their materias; ADMIN and FINANZAS see all
- Tests for aggregation queries, filtering, and scope enforcement

## Capabilities

### New Capabilities

- `audit-metrics-panel`: Aggregate read queries over AuditLog — actions per day, communication status, interactions by user/materia, last actions log. All read-only, paginated, tenant-scoped.

### Modified Capabilities

*(No existing specs are changing — this is a pure addition.)*

## Impact

- **Backend**: New service methods in `backend/app/audit/services.py`, new router in `backend/app/audit/routers/`, new schemas in `backend/app/audit/schemas.py`
- **Permissions**: Uses existing `auditoria:ver` permission; COORDINADOR requires additional scope resolution against their assigned materias
- **No new models or migrations** — reads only from `audit_log` and `materias` tables
- **Tests**: New test module at `backend/tests/audit/test_panel_metricas.py`
