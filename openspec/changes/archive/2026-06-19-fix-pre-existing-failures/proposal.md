## Why

The backend has 8 pre-existing test failures and 20 lint errors that block CI and reduce development velocity. These failures were introduced by recent changes (C-18 perfil/facturante field, C-11 padron-email migration, C-06 seed script) and a lingering mismatch between test and production JWT libraries. Fixing them restores green CI and enforces code quality standards.

## What Changes

- **JWT tests**: Replace `jose_jwt` (uninstalled library) with `jwt` (PyJWT) in `test_jwt.py` — 2 test fixes
- **Session endpoint crypto**: Encrypt email via `AES-256-GCM` in test helper `_create_user()` — 2 test fixes
- **PerfilResponse schema**: Add `facturante: bool = False` to Pydantic schema — 4 test fixes
- **Lint errors**: Fix 20 ruff violations across 5 files (unused imports, E402 import order, unused variables)

No new capabilities, no spec-level requirement changes — this is purely a quality/bugfix change.

## Capabilities

### New Capabilities
None — this change fixes existing code, does not introduce new functionality.

### Modified Capabilities
None — no spec-level requirement changes; all fixes are implementation/test corrections.

## Impact

- `backend/tests/core/test_jwt.py` — 2 lines changed
- `backend/tests/core/test_session_endpoint.py` — 1 line changed (encrypt call)
- `backend/app/schemas/perfil.py` — 1 field added
- `alembic/versions/021_padron_email_cifrado.py` — 1 unused import removed
- `backend/app/routers/padrones.py` — 1 unused import removed
- `backend/app/workers/comunicacion_worker.py` — import order fixed
- `scripts/seed_dev.py` — import order + 1 unused variable removed
- `backend/tests/test_padron.py` — 6 unused imports + 2 unused variables removed
