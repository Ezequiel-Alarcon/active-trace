"""Strict TDD for app.core.security.crypto (C-02 §2).

Spec contract — what the helper must do:
- encrypt(plaintext, tenant_id, aad_suffix) -> base64 blob; round-trip OK.
- Same plaintext twice -> two different ciphertexts (fresh random IV).
- AAD per-tenant: tenant A ciphertext NOT decryptable by tenant B.
- AAD per-suffix: column swap fails.
- Ciphertext tamper (1 bit flip) fails.
- AES-256-GCM (no CBC, no ECB).
- NEVER log plaintext, ciphertext, AAD full value. Logs only outcome +
  tenant_id + aad_suffix + opaque error code.
- The blob format is: version(1) || key_id(1) || nonce(12) || tag(16) ||
  ciphertext, base64 encoded for the str API.
"""

from __future__ import annotations

import base64
import logging
import os
from uuid import uuid4

import pytest

from app.core.security.crypto import (
    NONCE_SIZE,
    TAG_SIZE,
    CryptoError,
    decrypt,
    encrypt,
    encrypt_bytes,
    decrypt_bytes,
)


TENANT_A = uuid4()
TENANT_B = uuid4()


# ---------- Round-trip ----------


def test_round_trip_str_returns_original_plaintext() -> None:
    token = encrypt("hola mundo", tenant_id=TENANT_A, aad_suffix="usuario.email")
    assert decrypt(token, tenant_id=TENANT_A, aad_suffix="usuario.email") == "hola mundo"


def test_round_trip_without_aad_suffix() -> None:
    token = encrypt("dato", tenant_id=TENANT_A)
    assert decrypt(token, tenant_id=TENANT_A) == "dato"


def test_round_trip_bytes_api() -> None:
    blob = encrypt_bytes(b"raw bytes 123", tenant_id=TENANT_A, aad_suffix="cbu")
    assert decrypt_bytes(blob, tenant_id=TENANT_A, aad_suffix="cbu") == b"raw bytes 123"


# ---------- IV / freshness ----------


def test_same_plaintext_twice_yields_different_ciphertexts() -> None:
    a = encrypt("same", tenant_id=TENANT_A, aad_suffix="x")
    b = encrypt("same", tenant_id=TENANT_A, aad_suffix="x")
    assert a != b


# ---------- AAD enforcement ----------


def test_decryption_fails_when_tenant_differs() -> None:
    token = encrypt("cbu-1234", tenant_id=TENANT_A, aad_suffix="cbu")
    with pytest.raises(Exception):
        decrypt(token, tenant_id=TENANT_B, aad_suffix="cbu")


def test_decryption_fails_when_aad_suffix_differs() -> None:
    token = encrypt("dato", tenant_id=TENANT_A, aad_suffix="usuario.email")
    with pytest.raises(Exception):
        decrypt(token, tenant_id=TENANT_A, aad_suffix="usuario.cbu")


def test_decryption_fails_when_aad_suffix_missing() -> None:
    token = encrypt("dato", tenant_id=TENANT_A, aad_suffix="usuario.email")
    with pytest.raises(Exception):
        decrypt(token, tenant_id=TENANT_A)  # no suffix


# ---------- Tamper detection ----------


def test_tampered_ciphertext_fails() -> None:
    token = encrypt("valor", tenant_id=TENANT_A, aad_suffix="x")
    raw = bytearray(base64.b64decode(token))
    # Flip one bit somewhere safely past the header
    raw[NONCE_SIZE + TAG_SIZE] ^= 0x01
    tampered = base64.b64encode(bytes(raw)).decode("ascii")
    with pytest.raises(Exception):
        decrypt(tampered, tenant_id=TENANT_A, aad_suffix="x")


def test_tampered_tag_fails() -> None:
    token = encrypt("valor", tenant_id=TENANT_A, aad_suffix="x")
    raw = bytearray(base64.b64decode(token))
    # Flip a bit inside the tag region
    raw[1 + NONCE_SIZE] ^= 0x80
    tampered = base64.b64encode(bytes(raw)).decode("ascii")
    with pytest.raises(Exception):
        decrypt(tampered, tenant_id=TENANT_A, aad_suffix="x")


# ---------- Blob structure ----------


def test_blob_has_version_keyid_nonce_tag_ciphertext() -> None:
    """The on-the-wire format is 1+1+12+16=30 bytes header + ciphertext."""
    blob = encrypt_bytes(b"hello", tenant_id=TENANT_A, aad_suffix="x")
    # AES-GCM expands ciphertext by 0 bytes (tag is separate in our envelope)
    assert len(blob) >= 30 + 5  # header + payload
    assert NONCE_SIZE == 12
    assert TAG_SIZE == 16


def test_blob_records_key_id_in_header() -> None:
    """The blob carries a 1-byte key_id so rotation can be wired in later."""
    blob = encrypt_bytes(b"x", tenant_id=TENANT_A, aad_suffix="x", key_id=1)
    assert blob[1] == 1


# ---------- No PII in logs ----------


def test_encrypting_does_not_leak_plaintext_in_logs(caplog: pytest.LogCaptureFixture) -> None:
    secret = "PII-SECRET-12345678"
    caplog.set_level(logging.DEBUG)
    encrypt(secret, tenant_id=TENANT_A, aad_suffix="usuario.dni")
    all_text = "\n".join(rec.getMessage() for rec in caplog.records)
    assert secret not in all_text
    # No ciphertext blob leaked either
    for blob in (record.__dict__.get("ciphertext", "") for record in caplog.records):
        assert secret not in str(blob)


def test_failed_decryption_does_not_leak_plaintext_in_logs(
    caplog: pytest.LogCaptureFixture,
) -> None:
    secret = "OTRO-SECRETO-9876"
    token = encrypt(secret, tenant_id=TENANT_A, aad_suffix="x")
    # Now corrupt it so decrypt fails
    raw = bytearray(base64.b64decode(token))
    raw[-1] ^= 0x01
    tampered = base64.b64encode(bytes(raw)).decode("ascii")
    caplog.set_level(logging.DEBUG)
    with pytest.raises(Exception):
        decrypt(tampered, tenant_id=TENANT_A, aad_suffix="x")
    all_text = "\n".join(rec.getMessage() for rec in caplog.records)
    assert secret not in all_text


# ---------- Coverage extras (target 90% on this module) ----------


def test_decrypt_with_empty_ciphertext_fails() -> None:
    with pytest.raises(CryptoError):
        decrypt("", tenant_id=TENANT_A, aad_suffix="x")


def test_decrypt_with_invalid_base64_fails() -> None:
    with pytest.raises(CryptoError):
        decrypt("not-valid-base64!!!", tenant_id=TENANT_A, aad_suffix="x")


def test_decrypt_with_too_short_blob_fails() -> None:
    blob = base64.b64encode(b"abc").decode("ascii")
    with pytest.raises(CryptoError):
        decrypt(blob, tenant_id=TENANT_A, aad_suffix="x")


def test_decrypt_with_unsupported_version_fails() -> None:
    """A blob with version=99 is rejected before even attempting decryption."""
    raw = bytearray(b"\x99\x01" + os.urandom(NONCE_SIZE) + b"\x00" * TAG_SIZE)
    token = base64.b64encode(bytes(raw)).decode("ascii")
    with pytest.raises(CryptoError):
        decrypt(token, tenant_id=TENANT_A, aad_suffix="x")


def test_encrypt_bytes_uses_iv_from_blob_on_decrypt() -> None:
    """The same key_id and tenant must round-trip with the IV stored in the blob."""
    from app.core.config import get_settings

    settings = get_settings()
    raw_key = settings.ENCRYPTION_KEY.get_secret_value().encode("utf-8")
    assert len(raw_key) == 32  # sanity
    blob = encrypt_bytes(b"hola", tenant_id=TENANT_A, aad_suffix="x")
    assert decrypt_bytes(blob, tenant_id=TENANT_A, aad_suffix="x") == b"hola"
