## 1. Fix JWT Tests (2 failures)

- [x] 1.1 Replace `jose_jwt.encode()` with `jwt.encode()` in `test_jwt.py:132`
- [x] 1.2 Replace `jose_jwt.encode()` with `jwt.encode()` in `test_jwt.py:158`

## 2. Fix Session Endpoint Crypto (2 failures)

- [x] 2.1 Add `from app.core.security.crypto import encrypt` to `test_session_endpoint.py`
- [x] 2.2 Encrypt email in `_create_user()` at line 101: `email_enc=encrypt(email, tenant_id=tenant_id, aad_suffix="usuario.email")`

## 3. Fix PerfilResponse Schema (4 failures)

- [x] 3.1 Add `facturante: bool = False` field to `PerfilResponse` in `app/schemas/perfil.py`

## 4. Fix Lint Errors (20 violations)

- [x] 4.1 Remove unused `UUID` import from `alembic/versions/021_padron_email_cifrado.py`
- [x] 4.2 Remove unused `hash_email_for_search` import from `app/routers/padrones.py`
- [x] 4.3 Fix E402 (import order) in `app/workers/comunicacion_worker.py` — move imports before module-level code
- [x] 4.4 Fix E402 (import order) in `scripts/seed_dev.py` — move imports before `os.environ` setup + remove unused `GLOBAL_TENANT_ID`
- [x] 4.5 Remove 6 unused imports and 2 unused variables in `tests/test_padron.py`

## 5. Verify

- [x] 5.1 Run `pytest` to confirm 0 failures across the test suite
- [x] 5.2 Run `ruff check .` to confirm 0 lint violations
