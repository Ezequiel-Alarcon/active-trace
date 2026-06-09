"""Stable auth error codes (C-03 §3, D7).

The vocabulary is fixed — extend with care. The codes appear in:
- HTTPException headers (`X-Auth-Error-Code`) for client debugging.
- The structured audit log.
- The OpenAPI documentation.

Each `auth_error(...)` returns an `HTTPException` with the code baked in,
a non-leaky generic message, and optional `Retry-After` for rate-limited
responses.
"""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException

# Auth error vocabulary. EXTEND WITH CARE — codes are part of the public contract.
AUTH_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"
AUTH_2FA_REQUIRED = "AUTH_2FA_REQUIRED"
AUTH_2FA_INVALID = "AUTH_2FA_INVALID"
AUTH_TOKEN_MISSING = "AUTH_TOKEN_MISSING"
AUTH_TOKEN_INVALID = "AUTH_TOKEN_INVALID"
AUTH_TOKEN_REVOKED = "AUTH_TOKEN_REVOKED"
AUTH_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
AUTH_RATE_LIMITED = "AUTH_RATE_LIMITED"
AUTH_USER_DISABLED = "AUTH_USER_DISABLED"
AUTH_PASSWORD_RESET_INVALID = "AUTH_PASSWORD_RESET_INVALID"
AUTH_PASSWORD_RESET_USED = "AUTH_PASSWORD_RESET_USED"
AUTH_PASSWORD_RESET_EXPIRED = "AUTH_PASSWORD_RESET_EXPIRED"
AUTH_PASSWORD_TOO_SHORT = "AUTH_PASSWORD_TOO_SHORT"
AUTH_PASSWORD_REUSED = "AUTH_PASSWORD_REUSED"
AUTH_TENANT_NOT_FOUND = "AUTH_TENANT_NOT_FOUND"


_GENERIC_MESSAGES: dict[str, str] = {
    AUTH_INVALID_CREDENTIALS: "Invalid credentials.",
    AUTH_2FA_REQUIRED: "Two-factor authentication code required.",
    AUTH_2FA_INVALID: "Two-factor authentication code is invalid.",
    AUTH_TOKEN_MISSING: "Authentication required.",
    AUTH_TOKEN_INVALID: "Authentication token is invalid.",
    AUTH_TOKEN_REVOKED: "Authentication token is no longer valid.",
    AUTH_TOKEN_EXPIRED: "Authentication token has expired.",
    AUTH_RATE_LIMITED: "Too many attempts. Please try again later.",
    AUTH_USER_DISABLED: "Authentication failed.",
    AUTH_PASSWORD_RESET_INVALID: "Password reset link is invalid.",
    AUTH_PASSWORD_RESET_USED: "Password reset link has already been used.",
    AUTH_PASSWORD_RESET_EXPIRED: "Password reset link has expired.",
    AUTH_PASSWORD_TOO_SHORT: "Password does not meet the minimum length requirement.",
    AUTH_PASSWORD_REUSED: "New password must differ from the current password.",
    AUTH_TENANT_NOT_FOUND: "Authentication failed.",
}


def auth_error(code: str, status: int, **details: Any) -> HTTPException:
    """Build an HTTPException with a stable code and a non-leaky message."""
    message = _GENERIC_MESSAGES.get(code, "Authentication failed.")
    headers: dict[str, str] = {"X-Auth-Error-Code": code}
    retry_after = details.pop("retry_after", None)
    if retry_after is not None:
        headers["Retry-After"] = str(int(retry_after))
    body: dict[str, Any] = {"code": code, "message": message}
    body.update(details)
    return HTTPException(status_code=status, detail=body, headers=headers)
