## Context

The audit system (C-05) records every action in the append-only `audit_log` table. The existing `GET /api/audit/log` endpoint provides raw filtered listing with pagination. There is no aggregation layer — coordinators and admins cannot see usage trends, communication status summaries, or per-docente activity metrics without writing ad-hoc queries.

The `AuditLogService` currently has two read methods (`get_logs`, `get_impersonation_history`). We will extend it with four new aggregation methods. The `Materia` model is needed only for scope resolution (COORDINADOR `(propio)` can only see data for materias they coordinate).

## Goals / Non-Goals

**Goals:**
- Four new read-only aggregation endpoints under `/api/audit/`
- COORDINADOR `(propio)` scope enforcement via materia_id filtering
- All queries scoped by tenant (multi-tenancy row-level)
- MAX 500 LOC per file (backend rule)

**Non-Goals:**
- No new database models or migrations
- No write endpoints
- No frontend implementation
- No real-time streaming or websockets
- No caching layer (acceptable for current data volumes)

## Decisions

### Decision 1: New router file for metrics endpoints
- `backend/app/audit/routers/metrics.py` — keeps the existing `audit.py` clean, stays under 500 LOC
- Registered in `backend/app/audit/routers/__init__.py`

### Decision 2: Scope resolution for COORDINADOR (propio)
- The `request.state.permissions` set contains resolved permissions (from `require_permission` guard)
- If the user has `auditoria:ver_todos` (ADMIN/FINANZAS): no scope filter
- If the user has only `auditoria:ver` without `ver_todos`: resolve their materia_ids from the `equipo_docente` (docente assignments) table — they can only see audit data where `materia_id` matches their materias
- This mirrors the pattern used in avisos service (`Aviso.materia_id.in_(materia_ids)`)
- A new helper `_resolve_scope_materias` in the service layer queries materia IDs for the current user

### Decision 3: Aggregation queries use SQLAlchemy `func` directly
- No raw SQL needed — `func.date_trunc`, `func.count`, `func.date` for time series
- All queries are tenant-scoped by default
- Results serialized as new Pydantic response schemas

### Decision 4: Four new endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/audit/metrics/actions-per-day` | GET | Actions grouped by day, optional user filter |
| `/api/audit/metrics/comunicacion-status` | GET | Comms status counts by docente/materia |
| `/api/audit/metrics/interactions` | GET | Interaction counts by docente/materia/action |
| `/api/audit/metrics/last-actions` | GET | Last N audit entries, configurable limit |

### Decision 5: Response schemas live in `backend/app/audit/schemas.py`
- Avoid creating a new schemas file — existing file is under 100 LOC, comfortable room
- All new schemas use `extra="forbid"` (Pydantic rule)

## Risks / Trade-offs

- **Risk**: COORDINADOR scope query hits `equipo_docente` table each request → acceptable for current volumes; add a cache if profiling shows bottleneck
- **Risk**: `func.date_trunc` is PostgreSQL-specific → already our only DB, acceptable
- **Trade-off**: Keeping schemas in a single file vs splitting → single file is fine until it exceeds ~200 LOC; split if it grows
- **Trade-off**: No pagination on `/api/audit/metrics/last-actions` (uses `limit` param directly) → simple and sufficient for the panel use case
