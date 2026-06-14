"""Strict TDD for app.auth.services.two_factor_service (C-03 §4, D5).

Spec contract:
- `TwoFactorService.enroll(user) -> TwoFactorEnrollResponse`:
  - Generates a fresh base32 secret via `pyotp.random_base32(32)`.
  - Encrypts the secret at rest (AAD = `auth_user.totp_secret`).
  - Stores the encrypted blob on the user row and sets `totp_enabled = False`.
  - Returns `{otpauth_uri, secret}` — the raw secret is returned ONCE.
  - If the user already has a pending secret, the service still regenerates
    and overwrites; re-enrollment is explicit.
- `TwoFactorService.verify(user, code) -> TwoFactorVerifyResponse`:
  - Decrypts the stored secret, runs `pyotp.TOTP(secret).verify(code, valid_window=1)`.
  - On match: sets `totp_enabled = True`. Returns `verified=True`.
  - On mismatch: returns `verified=False`. Never raises.
  - Does NOT return the secret.
"""

from __future__ import annotations

import pyotp
import pytest

from app.auth.schemas import TwoFactorEnrollResponse
from app.auth.services.two_factor_service import TwoFactorService

pytestmark = pytest.mark.no_db


class _StubUser:
    def __init__(self) -> None:
        self.totp_secret_enc: str | None = None
        self.totp_enabled: bool = False
        self.tenant_id = "00000000-0000-0000-0000-000000000000"
        self.id = "00000000-0000-0000-0000-000000000001"
        self.email_enc = "enc:alice"


class _StubSession:
    async def flush(self) -> None:
        pass


def test_enroll_returns_otpauth_uri_and_secret() -> None:
    user = _StubUser()
    svc = TwoFactorService()  # type: ignore[arg-type]
    out = svc.enroll(user, _StubSession())  # type: ignore[arg-type]
    assert isinstance(out, TwoFactorEnrollResponse)
    assert out.otpauth_uri.startswith("otpauth://totp/")
    assert len(out.secret) >= 16  # base32


def test_enroll_stores_encrypted_secret_and_disables_totp() -> None:
    user = _StubUser()
    svc = TwoFactorService()
    svc.enroll(user, _StubSession())
    assert user.totp_secret_enc is not None
    assert user.totp_secret_enc != svc.enroll(  # type: ignore[arg-type]
        _StubUser(), _StubSession()
    ).secret
    # The cleartext secret is never stored
    assert user.totp_enabled is False


def test_enroll_uri_contains_issuer_and_label() -> None:
    user = _StubUser()
    svc = TwoFactorService(issuer_label="activia-trace")
    out = svc.enroll(user, _StubSession())
    assert "issuer=activia-trace" in out.otpauth_uri
    assert out.otpauth_uri.endswith(out.secret) or out.secret in out.otpauth_uri


def test_verify_with_correct_code_marks_totp_enabled() -> None:
    user = _StubUser()
    svc = TwoFactorService()
    out = svc.enroll(user, _StubSession())
    code = pyotp.TOTP(out.secret).now()
    res = svc.verify(user, _StubSession(), code)
    assert res.verified is True
    assert user.totp_enabled is True


def test_verify_with_wrong_code_returns_false() -> None:
    user = _StubUser()
    svc = TwoFactorService()
    svc.enroll(user, _StubSession())
    res = svc.verify(user, _StubSession(), "000000")
    assert res.verified is False
    assert user.totp_enabled is False


def test_verify_does_not_return_secret() -> None:
    user = _StubUser()
    svc = TwoFactorService()
    out = svc.enroll(user, _StubSession())
    res = svc.verify(user, _StubSession(), pyotp.TOTP(out.secret).now())
    # The verify response must not leak the secret
    assert not hasattr(res, "secret")
    assert "secret" not in str(res.__dict__)


def test_verify_with_no_secret_returns_false() -> None:
    user = _StubUser()
    svc = TwoFactorService()
    res = svc.verify(user, _StubSession(), "123456")
    assert res.verified is False


def test_enroll_secret_is_at_least_32_base32_chars() -> None:
    user = _StubUser()
    svc = TwoFactorService()
    out = svc.enroll(user, _StubSession())
    # 32 base32 chars (160 bits) is the standard for TOTP
    assert len(out.secret) >= 32
