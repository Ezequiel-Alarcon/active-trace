# Proposal: C-05 — Audit Log (E-AUD)

## Why

The system logs every significant action for accountability and traceability (the product is literally named *trace*). C-04's RBAC layer is now in place; C-05 adds the append-only audit log that records WHO did WHAT, WHEN, and on WHOSE behalf. This is the backbone of regulatory compliance and incident investigation. Without it, the system has no accountability even though the permission layer exists.

---

## What Changes

- **New table**: `audit_log` (E-AUD) — tenant-scoped, append-only (no UPDATE/DELETE at app or DB level).
- **Model `AuditLog`**: actor_id, impersonado_id, materia_id (nullable), accion (standardized code), detalle (JSON), filas_afectadas, ip, user_agent, fecha_hora.
- **Helper/decorator** `audit(action_code: str)` that wraps service methods and automatically records the action with full context.
- **Impersonation support**: `IMPERSONACION_INICIAR` and `IMPERSONACION_FINALIZAR` action codes; when active, `impersonado_id` is set on every audited action.
- **`impersonacion:usar` permission**: required to start/end impersonation sessions.
- **`GET /api/audit/log`** (requires `auditoria:ver`) — paginated, filterable by actor, accion, date range.
- **Migration 005**: `audit_log` table.
- **Tests**: append-only (update/delete rejected), impersonation attribution, action code recording.

---

## Capabilities

### New Capabilities

- **`audit-log-append-only`**: The `audit_log` table is append-only at the DB level (no UPDATE/DELETE path). The app enforces this via repository — no `update` or `delete` methods exist. Tests verify that update/delete raise errors.
- **`audit-log-decorator`**: `@audit("ACCION_CODIGO")` decorator that wraps service methods, automatically capturing actor, tenant, timestamp, IP, user agent, and action details.
- **`audit-log-impersonation`**: Impersonation session management. When a user with `impersonacion:usar` starts impersonation, every subsequent action records both the real actor and the impersonated user. `IMPERSONACION_INICIAR` / `IMPERSONACION_FINALIZAR` are recorded as special audit entries.
- **`audit-log-read-api`**: `GET /api/audit/log` endpoint (requires `auditoria:ver`). Paginated, filterable by `actor_id`, `accion`, `from`/`to` date, `impersonado_id`. COORDINADOR sees only their own tenant's logs; ADMIN sees all.

### Modified Capabilities

- **`auth-jwt-2fa`**: No requirement changes. The `AuthUser` model and `get_current_user` are extended to support impersonation state (whether the session is currently impersonating another user).

---

## Impact

| Area | Impact |
|------|--------|
| **Database** | New migration 005: `audit_log` table with indexes |
| **Every service** | Can use `@audit` decorator to log actions automatically |
| **C-04 RBAC** | `auditoria:ver` and `impersonacion:usar` permissions are seeded in the matrix |
| **C-06 estructura-academica** | Will use `@audit` for all CRUD operations |
| **Tests** | New integration tests for append-only enforcement, impersonation, and API |

---

## Out of Scope

- Audit log pruning or archival — infinite retention for v1.
- Export to external SIEM — future integration point.
- Real-time audit streaming (WebSocket) — future enhancement.
- Audit of audit reads (`auditoria:ver` calls) — not logged.