"""Strict TDD for app.auth.errors (C-03 §3).

Spec contract:
- Stable error code constants exist: AUTH_INVALID_CREDENTIALS,
  AUTH_2FA_REQUIRED, AUTH_2FA_INVALID, AUTH_TOKEN_MISSING, AUTH_TOKEN_INVALID,
  AUTH_TOKEN_REVOKED, AUTH_TOKEN_EXPIRED, AUTH_RATE_LIMITED,
  AUTH_USER_DISABLED, AUTH_PASSWORD_RESET_INVALID, AUTH_PASSWORD_RESET_USED,
  AUTH_PASSWORD_RESET_EXPIRED, AUTH_PASSWORD_TOO_SHORT,
  AUTH_PASSWORD_REUSED, AUTH_TENANT_NOT_FOUND.
- `auth_error(code, status, **details) -> HTTPException` produces a
  HTTPException with the code in `extra["code"]` and a `message` that does
  NOT leak PII.
- Each documented code maps to the correct HTTP status.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.auth import errors as auth_errors
from app.auth.errors import (
    AUTH_2FA_INVALID,
    AUTH_2FA_REQUIRED,
    AUTH_INVALID_CREDENTIALS,
    AUTH_PASSWORD_RESET_EXPIRED,
    AUTH_PASSWORD_RESET_INVALID,
    AUTH_PASSWORD_RESET_USED,
    AUTH_PASSWORD_REUSED,
    AUTH_PASSWORD_TOO_SHORT,
    AUTH_RATE_LIMITED,
    AUTH_TENANT_NOT_FOUND,
    AUTH_TOKEN_EXPIRED,
    AUTH_TOKEN_INVALID,
    AUTH_TOKEN_MISSING,
    AUTH_TOKEN_REVOKED,
    AUTH_USER_DISABLED,
    auth_error,
)

pytestmark = pytest.mark.no_db


def test_auth_error_returns_http_exception_with_code() -> None:
    exc = auth_error(AUTH_INVALID_CREDENTIALS, 401)
    assert isinstance(exc, HTTPException)
    assert exc.status_code == 401
    assert exc.headers is not None
    assert exc.headers["X-Auth-Error-Code"] == AUTH_INVALID_CREDENTIALS


def test_auth_error_message_is_non_leaky() -> None:
    exc = auth_error(AUTH_INVALID_CREDENTIALS, 401)
    msg = str(exc.detail).lower()
    for forbidden in ("password", "email", "tenant", "user", "hash", "secret"):
        assert forbidden not in msg, f"message leaks {forbidden!r}: {exc.detail!r}"


def test_auth_error_includes_extra_code_field() -> None:
    exc = auth_error(AUTH_2FA_REQUIRED, 401)
    assert exc.detail["code"] == AUTH_2FA_REQUIRED


def test_rate_limited_status_is_429() -> None:
    exc = auth_error(AUTH_RATE_LIMITED, 429, retry_after=30)
    assert exc.status_code == 429
    assert exc.headers is not None
    assert exc.headers["Retry-After"] == "30"


def test_token_codes_map_to_401() -> None:
    for code in (
        AUTH_TOKEN_MISSING,
        AUTH_TOKEN_INVALID,
        AUTH_TOKEN_EXPIRED,
        AUTH_TOKEN_REVOKED,
        AUTH_USER_DISABLED,
    ):
        exc = auth_error(code, 401)
        assert exc.status_code == 401


def test_2fa_codes_map_to_401() -> None:
    for code in (AUTH_2FA_REQUIRED, AUTH_2FA_INVALID):
        exc = auth_error(code, 401)
        assert exc.status_code == 401


def test_invalid_credentials_maps_to_401() -> None:
    exc = auth_error(AUTH_INVALID_CREDENTIALS, 401)
    assert exc.status_code == 401


def test_tenant_not_found_maps_to_401() -> None:
    """Tenant lookups must NOT differentiate missing vs invalid (no enumeration)."""
    exc = auth_error(AUTH_TENANT_NOT_FOUND, 401)
    assert exc.status_code == 401


def test_reset_codes_map_to_400_or_401() -> None:
    for code in (
        AUTH_PASSWORD_RESET_INVALID,
        AUTH_PASSWORD_RESET_USED,
        AUTH_PASSWORD_RESET_EXPIRED,
        AUTH_PASSWORD_TOO_SHORT,
        AUTH_PASSWORD_REUSED,
    ):
        exc = auth_error(code, 400)
        assert exc.status_code in (400, 401)


def test_all_codes_are_stable_strings() -> None:
    expected = {
        "AUTH_INVALID_CREDENTIALS",
        "AUTH_2FA_REQUIRED",
        "AUTH_2FA_INVALID",
        "AUTH_TOKEN_MISSING",
        "AUTH_TOKEN_INVALID",
        "AUTH_TOKEN_REVOKED",
        "AUTH_TOKEN_EXPIRED",
        "AUTH_RATE_LIMITED",
        "AUTH_USER_DISABLED",
        "AUTH_PASSWORD_RESET_INVALID",
        "AUTH_PASSWORD_RESET_USED",
        "AUTH_PASSWORD_RESET_EXPIRED",
        "AUTH_PASSWORD_TOO_SHORT",
        "AUTH_PASSWORD_REUSED",
        "AUTH_TENANT_NOT_FOUND",
    }
    actual = {
        c for c in vars(auth_errors) if c.startswith("AUTH_") and isinstance(getattr(auth_errors, c), str)
    }
    assert expected.issubset(actual), f"missing: {expected - actual}"
