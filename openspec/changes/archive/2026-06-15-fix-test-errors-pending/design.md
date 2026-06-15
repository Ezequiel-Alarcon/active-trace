# Design: C-04.1 — Fix Test Errors Pending

## Context

Four test bugs from C-01 through C-04, all producing failures in the full suite but passing in isolation. This is a pure test-infrastructure fix — no business logic changes, no new models, no new endpoints.

---

## Goals / Non-Goals

**Goals:**
- Full test suite (excluding known-flaky) passes: 193/193
- No test contaminates another
- Consistent transaction boundaries in repository mutating methods

**Non-Goals:**
- No changes to production code behavior
- No new functionality
- No changes to Alembic migration logic (only the test fixture that uses it)

---

## Decisions

### D1: Fix `_isolated_db` teardown — restore ORM tables after DROP SCHEMA

**Problem**: `_isolated_db` (module-scoped, autouse) runs `DROP SCHEMA public CASCADE` + `CREATE SCHEMA public`. After the alembic tests complete, the `public` schema is empty. All subsequent modules that rely on `Base.metadata.create_all`-created tables (`_smoke_tests`, `tenant`, `auth_user`, etc.) fail with `UndefinedTableError`.

**Fix**: After the alembic module's tests finish, the `_isolated_db` fixture's teardown (after `yield`) calls `_ensure_schema_sync()` again to restore all ORM-created tables.

```python
@pytest_asyncio.fixture(scope="module", autouse=True, loop_scope="module")
async def _isolated_db() -> None:
    await _drop_and_recreate_test_schema()
    yield  # tests run here
    # FIX: restore ORM tables for subsequent modules
    _ensure_schema_sync()
```

**Trade-off**: Running `_ensure_schema_sync()` twice (once at session start via `_apply_schema_once`, once in teardown) is acceptable — idempotent operation.

### D2: Fix `test_config.py` — guard `setdefault` with opt-out flag

**Problem**: `conftest.py` line 17 runs `os.environ.setdefault("DATABASE_URL", ...)` at import time. `test_config.py` does `monkeypatch.delenv("DATABASE_URL")` to test missing var — but `setdefault` already set the value, so the deletion has no effect and `Settings()` doesn't raise.

**Fix**: Guard the `setdefault` with a flag that `test_config.py` can set before import:

```python
# conftest.py
import sys as _sys
if "pydantic" not in _sys.modules:  # only set before Settings loads
    os.environ.setdefault("DATABASE_URL", "...")

# test_config.py — add at TOP of file, before any imports:
import sys
sys.modules["pydantic"] = None  # prevents conftest setdefault from running
# OR: use pytest marker @pytest.mark.no_db and fix _session_is_all_no_db logic
```

Actually, cleaner approach: mark `test_config.py` as `@pytest.mark.no_db` and ensure `_session_is_all_no_db` correctly detects it. But the user declined this before. Alternative: wrap the `setdefault` in a check:

```python
# conftest.py — line 17
if "DATABASE_URL" not in os.environ:  # only set if not already set
    os.environ["DATABASE_URL"] = "..."
```

But this changes the default behavior for normal test runs. The real issue: `setdefault` at module import time is wrong. Move it inside `_ensure_schema_sync()` where it's actually needed.

### D3: `revoke_active_for_user` — `flush()` → `commit()`

**Problem**: `AuthSessionRepository.revoke_active_for_user` (line 131) uses `flush()` while `revoke_chain` (line 119) and all other mutating methods use `commit()`. Inconsistent.

**Fix**: Change `await self._session.flush()` → `await self._session.commit()` in `revoke_active_for_user`. All mutating repository methods should commit, not flush, to ensure the transaction is persisted and visible to subsequent sessions in tests.

### D4: `test_jwt.py` flaky — isolate shared state

**Problem**: `test_decode_access_rejects_tampered_signature` passes in isolation but fails in the full suite. Likely shared module-level state pollution (possibly from `test_rate_limit.py` or another core test that modifies JWT configuration).

**Fix**: Add `cache_clear()` calls on any module-level caches in the JWT module before the test runs. Ensure each test gets a fresh `PyJWKSetClient` or similar shared object.

---

## Migration Plan

No migration — pure test fix. Run full suite before/after to confirm.

---

## Open Questions

| Question | Status |
|----------|--------|
| Q1: Should `_apply_schema_once` re-run if schema is missing mid-session? | Resolved: yes — add a check in `_apply_schema_once` to detect missing tables and re-create |
| Q2: Is the `flush()` vs `commit()` inconsistency causing actual bugs? | Likely not — but it makes tests unpredictable. Fix for consistency. |
| Q3: Is `test_jwt.py` flaky due to test pollution or async event loop issue? | Likely test pollution from module-level state. Fix with cache isolation. |