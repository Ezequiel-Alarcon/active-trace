# Proposal: C-04.1 — Fix Test Errors Pending

## Why

C-01 through C-04 introduced tests that passed in isolation but produced failures when run as a full suite. Four distinct bugs accumulated:

1. **`test_alembic_migration_001.py`'s `_isolated_db` fixture** drops the `public` schema and leaves it empty — subsequent tests (26 errors + 6 failures) cannot find their tables.
2. **`conftest.py`'s `os.environ.setdefault` at import time** makes `test_config.py`'s `monkeypatch.delenv` ineffective — 1 failure (was 5 in full suite).
3. **`AuthSessionRepository.revoke_active_for_user` uses `flush()`** while sibling methods use `commit()` — inconsistent transaction boundary.
4. **`test_jwt.py::test_decode_access_rejects_tampered_signature`** is flaky (passes in isolation, fails in suite) — test pollution from shared module state.

All four are test infrastructure bugs, not business logic. Governance: **BAJO** (test fixes only). No new functionality.

---

## What Changes

- **`tests/integration/test_alembic_migration_001.py`**: `_isolated_db` teardown restores `_smoke_tests` and all ORM-created tables via `Base.metadata.create_all`. Schema is clean for subsequent modules.
- **`tests/conftest.py`**: Move `os.environ.setdefault` for `DATABASE_URL` inside a helper that tests can opt out of, OR guard it with a `_TESTING_DB_URL_SET` flag. `test_config.py` gets `@pytest.mark.no_db`.
- **`app/auth/repositories.py`**: `revoke_active_for_user` changes `flush()` → `commit()` to match `revoke_chain` and all other mutating methods.
- **`tests/core/test_jwt.py`**: Isolate the flaky test — ensure no shared mutable state between test runs.

---

## Capabilities

### New Capabilities

- `test-fixture-isolation`: Fixes that ensure tests pass individually AND as a full suite.

### Modified Capabilities

(None — this change modifies existing spec behavior only at the test/fixture level, not at the requirement level.)

---

## Impact

| Area | Impact |
|------|--------|
| **Test suite** | 193 → 193 passing (errors fixed, no regressions) |
| **`test_alembic_migration_001.py`** | No longer contaminates subsequent modules |
| **`test_config.py`** | All 5 tests pass in isolation and in suite |
| **`test_revoke_active_for_user`** | Consistent transaction boundary |
| **`test_jwt.py`** | Deterministic (no more flaky failure) |