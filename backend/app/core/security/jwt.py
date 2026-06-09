"""JWT encode/decode for access and refresh tokens (C-03 §1, D1, D2).

Claims (access token):
- sub:  auth_user.id (UUID as string)
- tid:  auth_user.tenant_id (UUID as string)
- sid:  auth_session.id (UUID as string)
- iat:  issued-at (server clock, seconds)
- exp:  iat + ACCESS_TOKEN_EXPIRE_MINUTES
- jti:  per-token UUID
- typ:  "access" | "refresh"

Roles are NOT in the token (D1, decided for C-04 / re-login UX).
"""

from __future__ import annotations

import logging
import time
from typing import Any, Final
from uuid import UUID

from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError

from app.core.config import get_settings

logger = logging.getLogger("activia_trace.security.jwt")

_ALG: Final = "HS256"
_TYP_ACCESS: Final = "access"
_TYP_REFRESH: Final = "refresh"
_CLOCK_SKEW_SECONDS: Final = 30


class InvalidTokenError(Exception):
    """Raised for any token rejection (signature, expiry, typ, iat, malformed)."""


def _now() -> int:
    return int(time.time())


def _encode(
    typ: str,
    *,
    user_id: UUID,
    tenant_id: UUID,
    session_id: UUID,
    jti: UUID,
    expire_minutes: int,
) -> str:
    settings = get_settings()
    now_seconds = _now()
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "tid": str(tenant_id),
        "sid": str(session_id),
        "iat": now_seconds,
        "exp": now_seconds + expire_minutes * 60,
        "jti": str(jti),
        "typ": typ,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=_ALG)


def encode_access_token(
    *,
    user_id: UUID,
    tenant_id: UUID,
    session_id: UUID,
    jti: UUID,
) -> str:
    return _encode(
        _TYP_ACCESS,
        user_id=user_id,
        tenant_id=tenant_id,
        session_id=session_id,
        jti=jti,
        expire_minutes=get_settings().ACCESS_TOKEN_EXPIRE_MINUTES,
    )


def encode_refresh_token(
    *,
    user_id: UUID,
    tenant_id: UUID,
    session_id: UUID,
    jti: UUID,
) -> str:
    return _encode(
        _TYP_REFRESH,
        user_id=user_id,
        tenant_id=tenant_id,
        session_id=session_id,
        jti=jti,
        expire_minutes=get_settings().REFRESH_TOKEN_EXPIRE_MINUTES,
    )


def _decode(token: str, expected_typ: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        claims = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[_ALG],
            options={"verify_iat": True, "verify_exp": True},
        )
    except ExpiredSignatureError as exc:
        raise InvalidTokenError("token expired") from exc
    except JWTError as exc:
        raise InvalidTokenError("token verification failed") from exc

    typ = claims.get("typ")
    if typ != expected_typ:
        raise InvalidTokenError(f"expected typ={expected_typ}, got {typ!r}")

    iat = claims.get("iat")
    if iat is None:
        raise InvalidTokenError("missing iat claim")
    skew = _now() - iat
    if skew < -_CLOCK_SKEW_SECONDS:
        raise InvalidTokenError("iat is too far in the future")

    for required in ("sub", "tid", "sid", "jti", "exp"):
        if required not in claims:
            raise InvalidTokenError(f"missing claim: {required}")
    return claims


def decode_access_token(token: str) -> dict[str, Any]:
    return _decode(token, _TYP_ACCESS)


def decode_refresh_token(token: str) -> dict[str, Any]:
    return _decode(token, _TYP_REFRESH)
