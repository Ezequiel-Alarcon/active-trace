# Design: C-05 — Audit Log (E-AUD)

## Context

C-04 (RBAC) is complete. The permission layer exists and every endpoint declares `require_permission`. C-05 adds the accountability layer: an append-only audit log that records every significant action with full context (who, what, when, on whose behalf, from where).

The KB defines `AuditLog` (E-AUD) as: `actor_id`, `impersonado_id`, `materia_id`, `accion` (standardized code), `detalle` (JSON), `filas_afectadas`, `ip`, `user_agent`, `fecha_hora`.

The system must be able to answer: "What did user X do between dates A and B?" and "Who impersonated whom on date D?"

---

## Goals / Non-Goals

**Goals:**
- Append-only `audit_log` table — no UPDATE/DELETE at any layer.
- `@audit("ACCION_CODIGO")` decorator for service methods.
- Impersonation-aware: `impersonado_id` set when active.
- `GET /api/audit/log` with pagination and filters.
- `IMPERSONACION_INICIAR` / `IMPERSONACION_FINALIZAR` entries.
- Migration 005.

**Non-Goals:**
- Audit log of audit reads — `auditoria:ver` calls are not logged.
- Log pruning or archival.
- Real-time streaming.
- Export to external SIEM.

---

## Decisions

### D1: Append-only at repository level (not DB constraint)

**Decision**: The `AuditLogRepository` has no `update` or `delete` methods. The SQLAlchemy model has no mutators beyond constructor. No DB-level trigger enforcement needed — the app contract is sufficient.

**Rationale**: DB-level triggers can be bypassed by direct SQL. The app is the only writer; enforcing at the repository layer is the right place.

### D2: `@audit` decorator on service methods (not middleware)

**Decision**: Use a decorator `@audit("CALIFICACIONES_IMPORTAR")` applied to service methods. The decorator captures context from `request.state` (set by `require_permission` guard) and writes the audit entry.

**Rationale**: Middleware would log every HTTP request — too noisy. Decorating specific service methods gives precise control over what constitutes a "significant action". Business logic and audit are co-located.

### D3: Action codes as constants (not free-form strings)

**Decision**: Action codes are string constants defined in `app/audit/constants.py` (e.g., `AUDIT_CALIFICACIONES_IMPORTAR = "CALIFICACIONES_IMPORTAR"`). Repository validates against known codes on write.

**Rationale**: Prevents typos and ensures consistent reporting. Codes map to functional areas, not individual endpoints.

### D4: Impersonation stored in request state

**Decision**: When `require_permission` resolves permissions, it also checks if an impersonation session is active (from a separate `ImpersonationContext`). The context is stored in `request.state.impersonating` and `request.state.impersonated_user_id`. The `@audit` decorator reads these.

**Rationale**: Impersonation state is orthogonal to authentication. The JWT doesn't carry it (would be a security smell). It's a server-side session flag set via explicit `POST /api/impersonation/start` and `DELETE /api/impersonation/end`.

### D5: Audit log is tenant-scoped, readable by ADMIN or COORDINADOR (own tenant)

**Decision**: `audit_log.tenant_id` is set from the current tenant context. `GET /api/audit/log` requires `auditoria:ver`. ADMIN sees all tenants' logs; COORDINADOR sees only their own tenant.

**Rationale**: ADMIN needs cross-tenant visibility for support. COORDINADOR only needs their institution's logs.

---

## Data Model

```
Table: audit_log
  - id: UUID (PK)
  - tenant_id: UUID (FK → tenant, NOT NULL)
  - fecha_hora: TIMESTAMPTZ (NOT NULL, server-set)
  - actor_id: UUID (NOT NULL) — references AuthUser.id
  - impersonado_id: UUID (NULL) — NULL when no impersonation
  - materia_id: UUID (NULL)
  - accion: VARCHAR(64) (NOT NULL) — e.g., "CALIFICACIONES_IMPORTAR"
  - detalle: JSONB (NULL)
  - filas_afectadas: INTEGER (NOT NULL, default 0)
  - ip: VARCHAR(64) (NOT NULL)
  - user_agent: VARCHAR(512) (NOT NULL)

Indexes:
  - ix_audit_log_tenant_fecha (tenant_id, fecha_hora DESC) — primary query pattern
  - ix_audit_log_actor (actor_id)
  - ix_audit_log_accion (accion)
  - ix_audit_log_impersonado (impersonado_id)
```

---

## Impersonation Flow

```
1. Admin calls POST /api/impersonation/start {target_user_id}
   → requires permission impersonacion:usar
   → creates ImpersonationContext (actor_id, target_user_id, timestamp)
   → stores in request.state.impersonating = True, impersonated_user_id = target_user_id
   → writes AuditLog entry with accion = IMPERSONACION_INICIAR

2. Admin performs actions while impersonating
   → @audit decorator captures actor_id = real actor, impersonado_id = target
   → every audited action records both

3. Admin calls DELETE /api/impersonation/end
   → clears ImpersonationContext
   → writes AuditLog entry with accion = IMPERSONACION_FINALIZAR
```

---

## API Design

```
POST   /api/impersonation/start      { target_user_id }  (requires: impersonacion:usar)
DELETE /api/impersonation/end        —                   (requires: impersonacion:usar)
GET    /api/audit/log                ?actor=&accion=&from=&to=&page=  (requires: auditoria:ver)
```

---

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Audit decorator missed on some service methods | Make `@audit` the default pattern; code review enforces it |
| Performance: audit writes add latency to every action | Audit writes are fire-and-forget (async) — don't block the response |
| Large audit_log table affects query performance | Index on (tenant_id, fecha_hora DESC) handles most queries; partition by month if needed |
| Sensitive data in `detalle` JSON | Never log PII (DNI, CBU, password) — log only IDs and counts |

---

## Open Questions

| Question | Status |
|----------|--------|
| Q1: Should audit entries be written synchronously or via a background queue? | Resolved: async fire-and-forget for v1; queue if latency becomes an issue |
| Q2: Should `detalle` JSON have a schema? | Resolved: free-form JSONB; consumers parse as needed. Structured fields (actor, accion, rows) are columns. |
| Q3: Can COORDINADOR see impersonation entries? | Resolved: yes — impersonation is visible to the tenant's ADMIN/COORDINADOR |