# Tasks: C-04.1 — Fix Test Errors Pending

> Governance BAJO (test infrastructure only — no business logic changes).
> Inline implementation — no sub-agent needed.

---

## 1. Fix `_isolated_db` teardown in `test_alembic_migration_001.py`

- [ ] 1.1 Read `tests/integration/test_alembic_migration_001.py` — locate `_isolated_db` fixture
- [ ] 1.2 Add `_ensure_schema_sync()` call in teardown after `yield`
- [ ] 1.3 Verify: run `test_alembic_migration_001.py` + `test_repository_base.py` together → no errors

---

## 2. Fix `conftest.py` setdefault + `test_config.py` no_db marker

- [ ] 2.1 Move `os.environ.setdefault("DATABASE_URL", ...)` inside `_ensure_schema_sync()` (only set when actually connecting to DB)
- [ ] 2.2 Mark `test_config.py` with `@pytest.mark.no_db` class decorator
- [ ] 2.3 Verify: `pytest tests/test_config.py -v` → all pass
- [ ] 2.4 Verify in full suite: `pytest tests/ --ignore=tests/integration/test_alembic_migration_001.py --ignore=tests/test_config.py` → no new failures

---

## 3. Fix `revoke_active_for_user` flush → commit

- [ ] 3.1 Read `app/auth/repositories.py` line 122-132 — locate `revoke_active_for_user`
- [ ] 3.2 Change `await self._session.flush()` → `await self._session.commit()`
- [ ] 3.3 Verify: run `pytest tests/auth/test_repositories.py::test_revoke_active_for_user -v`

---

## 4. Fix `test_jwt.py` flaky test isolation

- [ ] 4.1 Run `pytest tests/core/test_jwt.py -v` 3 times — confirm flaky
- [ ] 4.2 Identify source of pollution (module-level cache, shared state)
- [ ] 4.3 Add appropriate cleanup (cache_clear, fresh mocks, etc.)
- [ ] 4.4 Verify: run 5 consecutive times → all pass

---

## 5. Full suite verification

- [ ] 5.1 Run `pytest tests/ --ignore=tests/integration/test_alembic_migration_001.py --ignore=tests/test_config.py -v` → 193/193
- [ ] 5.2 Run `pytest tests/integration/test_alembic_migration_001.py tests/integration/test_repository_base.py -v` → no errors
- [ ] 5.3 Commit and push