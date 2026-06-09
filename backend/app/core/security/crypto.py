"""AES-256-GCM PII encryption helper.

Design decisions live in `openspec/changes/core-models-y-tenancy/design.md` D4.

Contract (specs/pii-encryption):
- Round-trip on the same (tenant_id, aad_suffix) yields the original plaintext.
- AAD binds ciphertext to (tenant_id, aad_suffix) so a blob encrypted for one
  tenant (or one column) is rejected when decrypted by another.
- 96-bit random IV per call (GCM standard). Same plaintext + same key + same
  AAD -> two different ciphertexts.
- 1-bit flip in the stored ciphertext -> GCM auth tag mismatch -> failure.
- 32-byte key, validated at startup by Settings.
- The blob format is:
      version (1) || key_id (1) || nonce (12) || tag (16) || ciphertext
  `encrypt` returns this envelope base64-encoded as ASCII.
  `encrypt_bytes` returns the raw bytes.
- Logger `activia_trace.security.crypto` only emits outcome, tenant_id,
  aad_suffix, and an opaque error code on failure. NEVER plaintext, NEVER
  ciphertext, NEVER full AAD.
"""

from __future__ import annotations

import base64
import logging
import os
from typing import Final
from uuid import UUID

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import get_settings

NONCE_SIZE: Final = 12
TAG_SIZE: Final = 16
BLOB_VERSION: Final = 1
_HEADER_SIZE: Final = 1 + 1 + NONCE_SIZE + TAG_SIZE  # version + key_id + nonce + tag

logger = logging.getLogger("activia_trace.security.crypto")

# Public, fixed set of action codes the helper may emit. Keep aligned with
# the audit_emit seam in app.core.audit.
_OUTCOME_ENCRYPTED = "encrypted"
_OUTCOME_DECRYPTED = "decrypted"
_OUTCOME_FAILED = "failed"


# Reusable exception type for the caller boundary. Wrap cryptography's
# InvalidTag so callers (services, repositories) don't have to import the
# cryptography library to catch decrypt failures.
class CryptoError(Exception):
    """Raised when encryption/decryption fails for any reason (auth tag, format, key)."""


def _resolve_key(key_id: int) -> bytes:
    settings = get_settings()
    registry = settings.key_registry()
    if key_id not in registry:
        logger.warning(
            "crypto key lookup failed",
            extra={"action": _OUTCOME_FAILED, "key_id": key_id, "reason": "unknown_key"},
        )
        raise CryptoError(f"unknown key_id: {key_id}")
    return registry[key_id]


def _build_aad(tenant_id: UUID, aad_suffix: str | None) -> bytes:
    if aad_suffix is None:
        return str(tenant_id).encode("utf-8")
    return f"{tenant_id}:{aad_suffix}".encode("utf-8")


def _pack(version: int, key_id: int, nonce: bytes, tag: bytes, ciphertext: bytes) -> bytes:
    if len(nonce) != NONCE_SIZE:
        raise CryptoError(f"nonce must be {NONCE_SIZE} bytes, got {len(nonce)}")
    if len(tag) != TAG_SIZE:
        raise CryptoError(f"tag must be {TAG_SIZE} bytes, got {len(tag)}")
    return bytes([version, key_id]) + nonce + tag + ciphertext


def _unpack(blob: bytes) -> tuple[int, int, bytes, bytes, bytes]:
    if len(blob) < _HEADER_SIZE:
        raise CryptoError("blob too short")
    version = blob[0]
    key_id = blob[1]
    nonce = blob[2 : 2 + NONCE_SIZE]
    tag = blob[2 + NONCE_SIZE : 2 + NONCE_SIZE + TAG_SIZE]
    ciphertext = blob[_HEADER_SIZE:]
    return version, key_id, nonce, tag, ciphertext


def encrypt_bytes(
    plaintext: bytes,
    *,
    tenant_id: UUID,
    aad_suffix: str | None = None,
    key_id: int = 1,
) -> bytes:
    """Encrypt bytes; return the raw envelope (version|key_id|nonce|tag|ct)."""
    key = _resolve_key(key_id)
    nonce = os.urandom(NONCE_SIZE)
    aad = _build_aad(tenant_id, aad_suffix)
    aesgcm = AESGCM(key)
    # AESGCM.encrypt appends the tag to the ciphertext; we split them so the
    # envelope has a fixed-position tag for cheap tamper detection and stable
    # parsing in `decrypt_bytes`.
    ct_with_tag = aesgcm.encrypt(nonce, plaintext, aad)
    ciphertext = ct_with_tag[:-TAG_SIZE]
    tag = ct_with_tag[-TAG_SIZE:]
    logger.info(
        "crypto encrypt ok",
        extra={
            "action": _OUTCOME_ENCRYPTED,
            "tenant_id": str(tenant_id),
            "aad_suffix": aad_suffix,
            "key_id": key_id,
        },
    )
    return _pack(BLOB_VERSION, key_id, nonce, tag, ciphertext)


def decrypt_bytes(
    blob: bytes,
    *,
    tenant_id: UUID,
    aad_suffix: str | None = None,
) -> bytes:
    """Decrypt an envelope produced by `encrypt_bytes`. Raises CryptoError on failure."""
    try:
        version, key_id, nonce, tag, ciphertext = _unpack(blob)
    except CryptoError:
        logger.warning(
            "crypto decrypt failed",
            extra={
                "action": _OUTCOME_FAILED,
                "tenant_id": str(tenant_id),
                "aad_suffix": aad_suffix,
                "reason": "malformed_blob",
                "error_code": "E_MALFORMED",
            },
        )
        raise
    if version != BLOB_VERSION:
        logger.warning(
            "crypto decrypt failed",
            extra={
                "action": _OUTCOME_FAILED,
                "tenant_id": str(tenant_id),
                "aad_suffix": aad_suffix,
                "reason": "unsupported_version",
                "error_code": "E_VERSION",
                "blob_version": version,
            },
        )
        raise CryptoError(f"unsupported blob version: {version}")
    try:
        key = _resolve_key(key_id)
    except CryptoError:
        raise
    aad = _build_aad(tenant_id, aad_suffix)
    aesgcm = AESGCM(key)
    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext + tag, aad)
    except InvalidTag as exc:
        logger.warning(
            "crypto decrypt failed",
            extra={
                "action": _OUTCOME_FAILED,
                "tenant_id": str(tenant_id),
                "aad_suffix": aad_suffix,
                "reason": "auth_tag_mismatch",
                "error_code": "E_AUTHTAG",
            },
        )
        raise CryptoError("decryption failed: authentication tag mismatch") from exc
    logger.info(
        "crypto decrypt ok",
        extra={
            "action": _OUTCOME_DECRYPTED,
            "tenant_id": str(tenant_id),
            "aad_suffix": aad_suffix,
            "key_id": key_id,
        },
    )
    return plaintext


def encrypt(
    plaintext: str,
    *,
    tenant_id: UUID,
    aad_suffix: str | None = None,
    key_id: int = 1,
) -> str:
    """Encrypt a UTF-8 string; return base64(ASCII) of the envelope."""
    blob = encrypt_bytes(
        plaintext.encode("utf-8"),
        tenant_id=tenant_id,
        aad_suffix=aad_suffix,
        key_id=key_id,
    )
    return base64.b64encode(blob).decode("ascii")


def decrypt(
    ciphertext_b64: str,
    *,
    tenant_id: UUID,
    aad_suffix: str | None = None,
) -> str:
    """Decrypt a base64 envelope produced by `encrypt`; return the UTF-8 string."""
    try:
        blob = base64.b64decode(ciphertext_b64, validate=True)
    except Exception as exc:
        logger.warning(
            "crypto decrypt failed",
            extra={
                "action": _OUTCOME_FAILED,
                "tenant_id": str(tenant_id),
                "aad_suffix": aad_suffix,
                "reason": "base64_decode",
                "error_code": "E_B64",
            },
        )
        raise CryptoError("ciphertext is not valid base64") from exc
    return decrypt_bytes(blob, tenant_id=tenant_id, aad_suffix=aad_suffix).decode("utf-8")
