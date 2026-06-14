"""Strict TDD for app.core.security.passwords (C-03 §1).

Spec contract:
- `hash_password(plaintext) -> str` returns a non-empty string that is NOT the plaintext.
- The returned hash starts with the Argon2id PHC prefix (`$argon2id$`).
- `verify_password(plaintext, hash) -> bool` returns True for a matching pair, False for a wrong plaintext.
- `verify_password(plaintext, hash) -> bool` returns False for a tampered hash (no exception).
- `hash_password` is non-deterministic (two calls yield different hashes for the same plaintext).
- The PII rule: no plaintext, no hash bytes, no PHC prefix in the log records.
"""

from __future__ import annotations

import logging

import pytest

from app.core.security.passwords import hash_password, verify_password

pytestmark = pytest.mark.no_db


def test_hash_returns_non_empty_string() -> None:
    h = hash_password("correct-horse-battery-staple")
    assert isinstance(h, str)
    assert len(h) > 0
    assert h != "correct-horse-battery-staple"


def test_hash_uses_argon2id_phc_prefix() -> None:
    h = hash_password("secret-1234567890")
    assert h.startswith("$argon2id$"), f"expected argon2id prefix, got {h[:32]!r}"


def test_hash_is_non_deterministic() -> None:
    """Two calls with the same plaintext must produce two different hashes (random salt)."""
    a = hash_password("same-input")
    b = hash_password("same-input")
    assert a != b


def test_verify_password_matches_correct_plaintext() -> None:
    h = hash_password("correct-horse-battery-staple")
    assert verify_password("correct-horse-battery-staple", h) is True


def test_verify_password_rejects_wrong_plaintext() -> None:
    h = hash_password("correct-horse-battery-staple")
    assert verify_password("wrong", h) is False


def test_verify_password_rejects_tampered_hash() -> None:
    h = hash_password("correct-horse-battery-staple")
    tampered = h[:-1] + ("A" if h[-1] != "A" else "B")
    assert verify_password("correct-horse-battery-staple", tampered) is False


def test_verify_password_rejects_malformed_hash() -> None:
    assert verify_password("any", "not-an-argon2-hash") is False


def test_hash_does_not_leak_plaintext_in_logs(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG)
    secret = "VERY-UNIQUE-PASSWORD-XYZ-1234567890"
    hash_password(secret)
    all_text = "\n".join(rec.getMessage() for rec in caplog.records)
    assert secret not in all_text
