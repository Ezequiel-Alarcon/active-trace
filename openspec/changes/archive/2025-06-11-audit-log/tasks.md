# Tasks: C-05 — Audit Log (E-AUD)

> Strict TDD: test fails → code minimum → triangulate → refactor.
> No DB mocks. Use real DB (container or ephemeral).

---

## 1. Migration 005: audit_log table

- [ ] 1.1 Generate Alembic migration `005_audit_log.py`
- [ ] 1.2 Create `audit_log` table: `id` UUID PK, `tenant_id` UUID FK→tenant, `fecha_hora` TIMESTAMPTZ NOT NULL server-set, `actor_id` UUID NOT NULL, `impersonado_id` UUID NULL, `materia_id` UUID NULL, `accion` VARCHAR(64) NOT NULL, `detalle` JSONB NULL, `filas_afectadas` INTEGER NOT NULL default 0, `ip` VARCHAR(64) NOT NULL, `user_agent` VARCHAR(512) NOT NULL
- [ ] 1.3 Add indexes: `ix_audit_log_tenant_fecha` (tenant_id, fecha_hora DESC), `ix_audit_log_actor` (actor_id), `ix_audit_log_accion` (accion), `ix_audit_log_impersonado` (impersonado_id)
- [ ] 1.4 Verify migration: run `alembic upgrade head`, confirm `SELECT COUNT(*) FROM audit_log` returns 0 (empty at start)

---

## 2. AuditLog Model

- [ ] 2.1 Create `app/audit/models.py` with `AuditLog` model
  - All fields from migration, `fecha_hora` defaults to `func.now()`
  - No `update` or `delete` methods (append-only contract)
- [ ] 2.2 Register model in `app/models/__init__.py`
- [ ] 2.3 Verify model compiles and is discoverable by Alembic

---

## 3. AuditLogRepository

- [ ] 3.1 Create `app/audit/repositories.py`
  - `create(...) → AuditLog` — only mutating method
  - No `update()`, no `delete()`, no `soft_delete()` — append-only
- [ ] 3.2 Write test: create audit entry, verify no update method exists

---

## 4. Action Code Constants

- [ ] 4.1 Create `app/audit/constants.py`
  - `AUDIT_IMPERSONACION_INICIAR = "IMPERSONACION_INICIAR"`
  - `AUDIT_IMPERSONACION_FINALIZAR = "IMPERSONACION_FINALIZAR"`
  - `AUDIT_CALIFICACIONES_IMPORTAR = "CALIFICACIONES_IMPORTAR"`
  - `AUDIT_PADRON_CARGAR = "PADRON_CARGAR"`
  - `AUDIT_USUARIOS_GESTIONAR = "USUARIOS_GESTIONAR"`
  - etc.
- [ ] 4.2 Document action code format: `MODULO_ACCION` (uppercase, underscore)

---

## 5. `@audit` Decorator

- [ ] 5.1 Create `app/audit/decorator.py` with `@audit(action_code: str)` decorator
  - Reads `request.state.current_user`, `request.state.impersonating`, `request.state.impersonated_user_id`
  - Reads IP and user agent from request state (set by middleware)
  - Writes AuditLog entry via `AuditLogRepository.create()`
  - Fire-and-forget: catches exceptions and logs them, does not propagate
  - Works with both sync and async functions
- [ ] 5.2 Write unit tests: decorator captures context, async support, fire-and-forget, filas_afectadas from return value

---

## 6. Impersonation Context Middleware

- [ ] 6.1 Create `app/audit/impersonation.py` with `ImpersonationContext`
  - `start_impersonation(actor_id, target_user_id) → None` — sets request state
  - `end_impersonation() → None` — clears request state
  - `is_impersonating() → bool`
  - `get_impersonated_user_id() → UUID | None`
- [ ] 6.2 Add `request.state.impersonating` and `request.state.impersonated_user_id` population in `require_permission` guard (C-04 extend)
- [ ] 6.3 Write tests: start/end impersonation, state management

---

## 7. Impersonation API Endpoints

- [ ] 7.1 Create `app/audit/routers/impersonation.py`
  - `POST /api/impersonation/start` — requires `impersonacion:usar`, body `{target_user_id: UUID}`, writes IMPERSONACION_INICIAR audit entry
  - `DELETE /api/impersonation/end` — requires `impersonacion:usar`, writes IMPERSONACION_FINALIZAR audit entry
- [ ] 7.2 Register router in `app/api/v1/main_router.py`
- [ ] 7.3 Write integration tests: 403 without permission, audit entries created, state cleared on end

---

## 8. Audit Log Read API

- [ ] 8.1 Create `app/audit/routers/audit.py`
  - `GET /api/audit/log` — requires `auditoria:ver`
  - Query params: `page`, `page_size`, `actor`, `accion`, `from`, `to`, `all_tenants` (ADMIN only)
  - Paginated response: `{total, page, page_size, items: [...]}`
  - ADMIN can pass `all_tenants=true`; COORDINADOR always scoped to own tenant
- [ ] 8.2 Register router in `app/api/v1/main_router.py`
- [ ] 8.3 Write integration tests: pagination, filters, 403 without permission, ADMIN vs COORDINADOR scoping

---

## 9. Wire audit into existing services (extend C-04 endpoints)

- [ ] 9.1 Add `@audit` decorator to service methods in `app/rbac/services.py` (if any write operations exist)
- [ ] 9.2 Add `@audit` decorator to admin catalog service methods in `app/rbac/router.py`
- [ ] 9.3 Verify decorator works with existing C-04 RBAC service methods

---

## 10. Integration Tests — Full Audit Flow

- [ ] 10.1 Test: append-only — update/delete raises error
- [ ] 10.2 Test: @audit decorator captures all fields correctly
- [ ] 10.3 Test: impersonation INICIAR → FINALIZAR creates correct audit entries
- [ ] 10.4 Test: audited action during impersonation records impersonado_id
- [ ] 10.5 Test: GET /api/audit/log pagination and filters
- [ ] 10.6 Test: COORDINADOR sees only own tenant logs
- [ ] 10.7 Test: ADMIN with all_tenants=true sees all tenants
- [ ] 10.8 Run full integration suite → all pass

---

## 11. Verify and Archive

- [ ] 11.1 Run full test suite → ≥80% line coverage, all green
- [ ] 11.2 Commit and push C-05 branch
- [ ] 11.3 `/opsx:archive audit-log`
- [ ] 11.4 Mark `[x]` for C-05 in CHANGES.md