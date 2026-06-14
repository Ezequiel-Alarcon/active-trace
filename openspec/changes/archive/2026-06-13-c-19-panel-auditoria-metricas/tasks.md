## 1. Schemas

- [ ] 1.1 Add `ActionsPerDayResponse` schema (date: datetime, count: int)
- [ ] 1.2 Add `ComunicacionStatusItem` schema (materia_id, docente_id, pending, sending, ok, failed, cancelled)
- [ ] 1.3 Add `InteractionItem` schema (materia_id, docente_id, accion, count)
- [ ] 1.4 Add `LastActionsResponse` schema reusing `AuditLogResponse` with limit parameter

## 2. Service Layer — Aggregation Queries

- [ ] 2.1 Implement `get_actions_per_day(actor_id, from_date, to_date, materia_ids)` in `AuditLogService` using `func.date_trunc` and `func.count`
- [ ] 2.2 Implement `get_comunicacion_status(materia_ids)` grouping by materia_id and actor_id with status counts
- [ ] 2.3 Implement `get_interactions_summary(materia_ids)` grouping by materia_id, actor_id, accion
- [ ] 2.4 Implement `get_last_actions(limit, materia_ids)` returning most recent entries
- [ ] 2.5 Add `_resolve_scope_materias(usuario_id)` helper to query equipo_docente for COORDINADOR scope

## 3. Router

- [ ] 3.1 Create `backend/app/audit/routers/metrics.py` with four GET endpoints under `/api/audit/metrics/`
- [ ] 3.2 Wire each endpoint with `require_permission("auditoria:ver")` and scope resolution
- [ ] 3.3 Register `metrics_router` in `backend/app/audit/routers/__init__.py`

## 4. Tests

- [ ] 4.1 Write test `test_actions_per_day_returns_grouped_counts`
- [ ] 4.2 Write test `test_actions_per_day_filters_by_actor`
- [ ] 4.3 Write test `test_actions_per_day_respects_tenant_scope`
- [ ] 4.4 Write test `test_comunicacion_status_returns_grouped_counts`
- [ ] 4.5 Write test `test_interactions_summary_returns_grouped_counts`
- [ ] 4.6 Write test `test_last_actions_returns_most_recent`
- [ ] 4.7 Write test `test_last_actions_respects_limit`
- [ ] 4.8 Write test `test_coordinador_scope_filters_by_materia`
- [ ] 4.9 Write test `test_admin_sees_all_data`
