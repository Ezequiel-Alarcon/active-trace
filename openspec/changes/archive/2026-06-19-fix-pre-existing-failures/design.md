## Context

The backend has 8 pre-existing test failures and 20 lint errors introduced by recent changes (C-18 perfil, C-11 padron-email, C-06 seed) and a lingering jose→PyJWT migration gap. These failures block CI and degrade code quality.

## Goals / Non-Goals

**Goals:**
- Restore green test suite (8 failures → 0)
- Eliminate all ruff lint violations (20 → 0)
- Minimal, targeted changes — no refactoring beyond what's needed

**Non-Goals:**
- No new functionality or API changes
- No spec-level requirement changes
- No dependency additions or removals

## Decisions

1. **PyJWT over jose**: Production code already migrated to `import jwt` (PyJWT ≥2.8.0). Tests still use `from jose import jwt` which isn't installed. Fix: align tests with production.
2. **Encrypt in test helper**: `_create_user()` stores plaintext `email_enc`; the production `AuthService.get_session_data()` expects AES-256-GCM ciphertext. Fix: call `encrypt()` in the test helper — minimal change, tests mirror real flow.
3. **Add facturante to PerfilResponse**: `decrypt_usuario_fields()` already returns `facturante`, but the Pydantic schema rejects it with `extra="forbid"`. Fix: add the field with correct default — the schema was simply incomplete.
4. **4 separate lint fixes**: Each file has an isolated violation — fix each independently. No shared pattern needing abstraction.

## Risks / Trade-offs

- [Minimal change risk] Each fix is a 1-3 line change in a single file; rollback is trivial.
- [Test coverage] The fixes only address existing tests — no new test coverage is added. Acceptable since this is a bugfix-only change.
