# Tasks: fix-test-errors-pending — Fix all pre-existing test failures

> Governance BAJO (test infrastructure + bug fixes — no business logic changes).
> All 636 tests passing after this change.

---

## 1. Fix migration ENUM lifecycle (015, 016, 018, 019)

- [x] 1.1 `015_comunicacion.py`: DO $$ block + pg_ENUM(create_type=False) + DROP TYPE in downgrade
- [x] 1.2 `016_evaluaciones.py`: DO $$ blocks for 3 ENUMs + pg_ENUM(create_type=False) + DROP TYPE in downgrade
- [x] 1.3 `018_avisos.py`: DO $$ blocks for 2 ENUMs + pg_ENUM(create_type=False) + DROP TYPE in downgrade
- [x] 1.4 `019_tareas.py`: DO $$ block + pg_ENUM(create_type=False)

---

## 2. Fix test schema teardown (drop_all → CASCADE SQL)

- [x] 2.1 Replace `Base.metadata.drop_all` + FK loop with DO $$ CASCADE SQL in all conftest/test files
- [x] 2.2 Files fixed: tareas, rbac, estructura, padrones, analisis, avisos, perfil, mensajes, calificaciones, programas_fechas, audit_api, panel_metricas, test_padron, test_equipos, test_asignacion_api, test_usuario_api, test_usuario_models

---

## 3. Fix Alembic integration test runner

- [x] 3.1 Replace hardcoded `ALEMBIC_EXE` with `sys.executable, "-m", "alembic"` in 3 migration tests
- [x] 3.2 Pre-create `alembic_version (version_num VARCHAR(256))` before running alembic (was VARCHAR(32))
- [x] 3.3 `test_estructura/test_migration.py`: downgrade to `"004_rbac"` instead of `"-1"` to actually drop estructura tables

---

## 4. Fix EntradaPadron email rename (C-09 breaking change)

- [x] 4.1 `test_padron_integration.py`: use `decrypt_entrada_email()` instead of `.email` attribute
- [x] 4.2 `test_padron_integration.py`: key `usuario_ids_by_email` dict by `email_hash`, not plain email
- [x] 4.3 `test_padron.py`: add `suffix` param to `_seed_tenant` to avoid UniqueViolation in multi-tenant tests

---

## 5. Fix Calificacion model JSON null semantics

- [x] 5.1 `Calificacion.nota`: changed from `JSON` to `JSON(none_as_null=True)` so Python `None` → SQL NULL (not JSON null)
- [x] 5.2 This fixed `test_ranking_ordena_por_cantidad_aprobadas` counting nota=None as "approved"

---

## 6. Fix FastAPI cached engine / Event loop is closed

- [x] 6.1 Added `_reset_app_engine_async` fixture to root conftest (non-autouse)
- [x] 6.2 Injected into `db_setup` in `test_audit_api.py`, `test_panel_metricas.py`, `test_estructura/test_rbac.py`
- [x] 6.3 Added try/except on `engine.dispose()` in `test_estructura/test_rbac.py`

---

## 7. Fix AuditLogService.get_logs() query bug

- [x] 7.1 Fixed Python ternary operator precedence bug: `select(X).where(y) if y else select(X)` evaluated `bool(y)` on SQLAlchemy clause → TypeError
- [x] 7.2 Fixed missing `order_by`/`limit`/`offset` when filters were present (only applied in the `else` branch)

---

## 8. Full suite verification

- [x] 8.1 636 passed, 1 skipped, 0 failed
