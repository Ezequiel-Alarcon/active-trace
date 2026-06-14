"""Strict TDD for app.auth.schemas (C-03 §3).

Spec contract:
- All DTOs use `model_config = ConfigDict(extra='forbid')`.
- LoginRequest, LoginResponse, RefreshRequest, LogoutResponse,
  ForgotRequest, ResetRequest, TwoFactorEnrollResponse,
  TwoFactorVerifyRequest, TwoFactorVerifyResponse are defined.
- `extra='forbid'` rejects unknown fields with a validation error.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.auth.schemas import (
    ForgotRequest,
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    RefreshRequest,
    ResetRequest,
    TwoFactorEnrollResponse,
    TwoFactorVerifyRequest,
    TwoFactorVerifyResponse,
)

pytestmark = pytest.mark.no_db


def test_login_request_accepts_documented_fields() -> None:
    r = LoginRequest(
        tenant_codigo="UBA",
        email="alice@example.com",
        password="p",
    )
    assert r.tenant_codigo == "UBA"
    assert r.email == "alice@example.com"


def test_login_request_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        LoginRequest(
            tenant_codigo="UBA", email="a@b.com", password="p", intruder="x"
        )


def test_login_request_accepts_optional_totp_code() -> None:
    r = LoginRequest(tenant_codigo="UBA", email="a@b.com", password="p", totp_code="123456")
    assert r.totp_code == "123456"


def test_refresh_request_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        RefreshRequest(refresh_token="t", extra=1)  # type: ignore[call-arg]


def test_refresh_request_accepts_only_refresh_token() -> None:
    r = RefreshRequest(refresh_token="t")
    assert r.refresh_token == "t"


def test_logout_response_has_ok() -> None:
    r = LogoutResponse()
    assert r.ok is True


def test_forgot_request_minimal() -> None:
    r = ForgotRequest(tenant_codigo="UBA", email="a@b.com")
    assert r.tenant_codigo == "UBA"


def test_reset_request_minimal() -> None:
    r = ResetRequest(
        tenant_codigo="UBA",
        selector="ABCDEFGH",
        token="t",
        new_password="p" * 12,
    )
    assert r.selector == "ABCDEFGH"


def test_two_factor_enroll_response_has_required_fields() -> None:
    r = TwoFactorEnrollResponse(
        otpauth_uri="otpauth://totp/x",
        secret="BASE32SECRET",
    )
    assert r.secret == "BASE32SECRET"


def test_two_factor_verify_request() -> None:
    r = TwoFactorVerifyRequest(code="123456")
    assert r.code == "123456"


def test_two_factor_verify_response() -> None:
    r = TwoFactorVerifyResponse(verified=True)
    assert r.verified is True


def test_login_response_has_tokens() -> None:
    r = LoginResponse(
        access_token="a",
        refresh_token="b",
        token_type="bearer",
        expires_in=900,
        requires_2fa=False,
    )
    assert r.token_type == "bearer"
    assert r.expires_in == 900
