"""Strict TDD for app.core.security.jwt (C-03 §1).

Spec contract (D1, D2):
- `encode_access_token(user_id, tenant_id, session_id, jti) -> str` returns a JWT
  with claims `sub`, `tid`, `sid`, `iat`, `exp`, `jti`, `typ="access"`.
- `encode_refresh_token(...)` returns a JWT with the same claims plus `typ="refresh"`.
- `decode_access_token(token) -> dict` verifies signature, `typ`, `exp`.
  Returns the claims dict. Raises `InvalidTokenError` on any failure.
- `decode_refresh_token(token) -> dict` does the same for refresh tokens.
- `InvalidTokenError` is a single exception class; no library leak in service signatures.
- The decoder is strict: a token signed with a different key fails.
- The decoder is strict: an expired token fails.
- The decoder is strict: a refresh token presented to the access decoder is rejected.
- The decoder is strict: an access token presented to the refresh decoder is rejected.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

pytestmark = pytest.mark.no_db

from app.core.config import get_settings
from app.core.security.jwt import (
    InvalidTokenError,
    decode_access_token,
    decode_refresh_token,
    encode_access_token,
    encode_refresh_token,
)


def test_encode_access_token_returns_string_with_three_dot_parts() -> None:
    uid = uuid4()
    tid = uuid4()
    sid = uuid4()
    jti = uuid4()
    token = encode_access_token(user_id=uid, tenant_id=tid, session_id=sid, jti=jti)
    assert isinstance(token, str)
    parts = token.split(".")
    assert len(parts) == 3, f"JWT must have 3 parts, got {len(parts)}"


def test_decode_access_token_returns_documented_claims() -> None:
    uid = uuid4()
    tid = uuid4()
    sid = uuid4()
    jti = uuid4()
    token = encode_access_token(user_id=uid, tenant_id=tid, session_id=sid, jti=jti)
    claims = decode_access_token(token)
    assert claims["sub"] == str(uid)
    assert claims["tid"] == str(tid)
    assert claims["sid"] == str(sid)
    assert claims["jti"] == str(jti)
    assert claims["typ"] == "access"
    assert "iat" in claims
    assert "exp" in claims
    assert claims["exp"] > claims["iat"]


def test_encode_refresh_token_has_typ_refresh() -> None:
    uid = uuid4()
    tid = uuid4()
    sid = uuid4()
    jti = uuid4()
    token = encode_refresh_token(user_id=uid, tenant_id=tid, session_id=sid, jti=jti)
    claims = decode_refresh_token(token)
    assert claims["typ"] == "refresh"


def test_decode_access_rejects_refresh_token() -> None:
    token = encode_refresh_token(user_id=uuid4(), tenant_id=uuid4(), session_id=uuid4(), jti=uuid4())
    with pytest.raises(InvalidTokenError):
        decode_access_token(token)


def test_decode_refresh_rejects_access_token() -> None:
    token = encode_access_token(user_id=uuid4(), tenant_id=uuid4(), session_id=uuid4(), jti=uuid4())
    with pytest.raises(InvalidTokenError):
        decode_refresh_token(token)


def test_decode_access_rejects_garbage_token() -> None:
    with pytest.raises(InvalidTokenError):
        decode_access_token("not-a-jwt")


def test_decode_access_rejects_tampered_signature() -> None:
    token = encode_access_token(
        user_id=uuid4(), tenant_id=uuid4(), session_id=uuid4(), jti=uuid4()
    )
    # Flip one char in the signature segment
    head, payload, sig = token.split(".")
    tampered = ".".join([head, payload, sig[:-1] + ("A" if sig[-1] != "A" else "B")])
    with pytest.raises(InvalidTokenError):
        decode_access_token(tampered)


def test_decode_access_rejects_token_signed_with_different_key(monkeypatch) -> None:
    """A token issued with a different SECRET_KEY must be rejected."""
    from app.core import security

    settings = get_settings()
    original_key = settings.SECRET_KEY
    try:
        # Use the production encoder to get a valid token
        token = encode_access_token(
            user_id=uuid4(), tenant_id=uuid4(), session_id=uuid4(), jti=uuid4()
        )
        # Swap to a different key and force re-load of cached modules
        monkeypatch.setattr(settings, "SECRET_KEY", "z" * 32)
        # The encode function reads the key at call time, so the next decode
        # (using the swapped key) should fail to verify the previous token.
        with pytest.raises(InvalidTokenError):
            decode_access_token(token)
    finally:
        monkeypatch.setattr(settings, "SECRET_KEY", original_key)
        _ = security  # keep import alive


def test_decode_access_rejects_expired_token(monkeypatch) -> None:
    """A token with exp in the past is rejected."""
    # Encode with a 1-minute window, then move "now" forward by hand.
    token = encode_access_token(
        user_id=uuid4(), tenant_id=uuid4(), session_id=uuid4(), jti=uuid4()
    )
    # Patch ACCESS_TOKEN_EXPIRE_MINUTES to 0 by overriding the module's
    # _now_offset clock: we can simulate expiry by waiting — too slow.
    # Instead, generate a token that's already expired by manually crafting
    # a JWT with exp < iat. We use the encoder; if the encoder respects a
    # negative window, we get an expired token. If not, we use the
    # library directly to craft one.
    from jose import jwt as jose_jwt

    past = datetime.now(tz=timezone.utc) - timedelta(minutes=1)
    expired = jose_jwt.encode(
        {
            "sub": str(uuid4()),
            "tid": str(uuid4()),
            "sid": str(uuid4()),
            "jti": str(uuid4()),
            "iat": past - timedelta(minutes=1),
            "exp": past,
            "typ": "access",
        },
        get_settings().SECRET_KEY,
        algorithm="HS256",
    )
    with pytest.raises(InvalidTokenError):
        decode_access_token(expired)


def test_decode_access_rejects_token_with_iat_in_future(monkeypatch) -> None:
    """A token with iat noticeably in the future (clock skew beyond tolerance) is rejected.

    The contract says: iat is verified against the server clock with a small
    tolerance (default 30s). A token with iat 10 minutes in the future MUST fail.
    """
    from jose import jwt as jose_jwt

    future = datetime.now(tz=timezone.utc) + timedelta(minutes=10)
    bad = jose_jwt.encode(
        {
            "sub": str(uuid4()),
            "tid": str(uuid4()),
            "sid": str(uuid4()),
            "jti": str(uuid4()),
            "iat": future,
            "exp": future + timedelta(minutes=15),
            "typ": "access",
        },
        get_settings().SECRET_KEY,
        algorithm="HS256",
    )
    with pytest.raises(InvalidTokenError):
        decode_access_token(bad)


def test_decode_access_token_no_plaintext_in_logs(caplog: pytest.LogCaptureFixture) -> None:
    import logging

    caplog.set_level(logging.DEBUG)
    token = encode_access_token(
        user_id=uuid4(), tenant_id=uuid4(), session_id=uuid4(), jti=uuid4()
    )
    # Decode it
    decode_access_token(token)
    all_text = "\n".join(rec.getMessage() for rec in caplog.records)
    assert token not in all_text
