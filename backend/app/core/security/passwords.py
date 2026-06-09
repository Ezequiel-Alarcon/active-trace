"""Argon2id password hashing wrapper (C-03 §1, D3).

Pinned parameters: time_cost=3, memory_cost=64*1024 KiB, parallelism=4.

PII rule: never log the plaintext, the hash bytes, or the PHC prefix.
"""

from __future__ import annotations

import logging

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

logger = logging.getLogger("activia_trace.security.passwords")

_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=64 * 1024,
    parallelism=4,
)


def hash_password(plaintext: str) -> str:
    """Return the Argon2id PHC-encoded hash of `plaintext`."""
    return _hasher.hash(plaintext)


def verify_password(plaintext: str, encoded_hash: str) -> bool:
    """Constant-time verify. Returns False on any failure (no exception)."""
    try:
        return _hasher.verify(encoded_hash, plaintext)
    except (VerifyMismatchError, InvalidHashError):
        return False
    except Exception:
        logger.warning("password verify failed: malformed input")
        return False
