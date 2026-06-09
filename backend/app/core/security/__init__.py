"""Security package.

C-02: AES-256-GCM PII encryption (this module).
C-03+: JWT auth, Argon2id password hashing.
"""

from app.core.security.crypto import (
    NONCE_SIZE,
    TAG_SIZE,
    decrypt,
    decrypt_bytes,
    encrypt,
    encrypt_bytes,
)

__all__ = [
    "NONCE_SIZE",
    "TAG_SIZE",
    "encrypt",
    "decrypt",
    "encrypt_bytes",
    "decrypt_bytes",
]
