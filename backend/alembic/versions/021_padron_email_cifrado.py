"""021: padron email cifrado (C-09).

Replaces `entrada_padron.email` (plaintext) with:
  - `email_hash` VARCHAR(64)  NOT NULL  -- deterministic HMAC for lookups
  - `email_enc`  VARCHAR(2048) NOT NULL -- AES-256-GCM ciphertext

Migration steps:
  1. Add columns nullable
  2. Migrate existing rows: compute hash+enc per tenant_id
  3. Drop old `email` column
  4. Set NOT NULL on new columns

Downgrade:
  1. Add `email` nullable
  2. Decrypt existing rows back to plaintext
  3. Drop `email_hash`, `email_enc`
  4. Set NOT NULL on `email`

Run order:
    alembic upgrade head
    alembic downgrade -1
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


revision: str = "021_padron_email_cifrado"
down_revision: Union[str, None] = "020_mensajes_internos"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_AAD_EMAIL = "entrada_padron.email"
_NONCE_SIZE = 12
_TAG_SIZE = 16
_BLOB_VERSION = 1


def _get_key() -> bytes:
    """Load ENCRYPTION_KEY from env (same as app.core.config.Settings.key_registry)."""
    raw = os.environ.get("ENCRYPTION_KEY", "")
    if not raw:
        raise RuntimeError("ENCRYPTION_KEY not set; cannot migrate PII")
    key_bytes = raw.encode("utf-8")
    if len(key_bytes) < 16:
        raise RuntimeError(f"ENCRYPTION_KEY too short: {len(key_bytes)} bytes")
    # Pad/trim to 32 bytes (AES-256)
    return key_bytes.ljust(32, b"\x00")[:32]


def _hash_email(email_lower: str, tenant_id: str) -> str:
    key = _get_key()
    msg = f"{tenant_id}:{email_lower}".encode("utf-8")
    return hmac.new(key, msg, hashlib.sha256).hexdigest()


def _encrypt_email(email_lower: str, tenant_id: str) -> str:
    """AES-256-GCM encrypt. Mirrors app.core.security.crypto.encrypt."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    key = _get_key()
    nonce = os.urandom(_NONCE_SIZE)
    aad = f"{tenant_id}:{_AAD_EMAIL}".encode("utf-8")
    aesgcm = AESGCM(key)
    plaintext = email_lower.encode("utf-8")
    ct_with_tag = aesgcm.encrypt(nonce, plaintext, aad)
    ciphertext = ct_with_tag[:-_TAG_SIZE]
    tag = ct_with_tag[-_TAG_SIZE:]
    blob = bytes([_BLOB_VERSION, 1]) + nonce + tag + ciphertext
    return base64.b64encode(blob).decode("ascii")


def _decrypt_email(email_enc: str, tenant_id: str) -> str:
    """AES-256-GCM decrypt. Mirrors app.core.security.crypto.decrypt."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    key = _get_key()
    blob = base64.b64decode(email_enc, validate=True)
    # version + key_id + nonce + tag + ciphertext
    nonce = blob[2:2 + _NONCE_SIZE]
    tag = blob[2 + _NONCE_SIZE:2 + _NONCE_SIZE + _TAG_SIZE]
    ciphertext = blob[2 + _NONCE_SIZE + _TAG_SIZE:]
    aad = f"{tenant_id}:{_AAD_EMAIL}".encode("utf-8")
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext + tag, aad)
    return plaintext.decode("utf-8")


def upgrade() -> None:
    # 1. Add new columns as nullable
    op.add_column("entrada_padron", sa.Column("email_hash", sa.String(64), nullable=True))
    op.add_column("entrada_padron", sa.Column("email_enc", sa.String(2048), nullable=True))
    op.create_index(
        "ix_entrada_padron_tenant_email_hash",
        "entrada_padron",
        ["tenant_id", "email_hash"],
    )

    # 2. Migrate existing rows: read email per row, compute hash+enc
    conn = op.get_bind()
    rows = conn.execute(
        text("SELECT id, tenant_id, email FROM entrada_padron WHERE deleted_at IS NULL")
    ).fetchall()

    for row in rows:
        row_id, tenant_id, email_plain = row[0], str(row[1]), (row[2] or "").strip().lower()
        email_hash = _hash_email(email_plain, tenant_id)
        email_enc = _encrypt_email(email_plain, tenant_id)
        conn.execute(
            text(
                "UPDATE entrada_padron SET email_hash = :h, email_enc = :e WHERE id = :id"
            ),
            {"h": email_hash, "e": email_enc, "id": row_id},
        )

    # 3. Drop old column
    op.drop_column("entrada_padron", "email")

    # 4. Set NOT NULL
    op.alter_column("entrada_padron", "email_hash", nullable=False)
    op.alter_column("entrada_padron", "email_enc", nullable=False)


def downgrade() -> None:
    # 1. Add email column nullable
    op.add_column("entrada_padron", sa.Column("email", sa.String(2048), nullable=True))

    # 2. Decrypt existing rows back to plaintext
    conn = op.get_bind()
    rows = conn.execute(
        text("SELECT id, tenant_id, email_enc FROM entrada_padron WHERE deleted_at IS NULL")
    ).fetchall()

    for row in rows:
        row_id, tenant_id, email_enc = row[0], str(row[1]), row[2]
        if email_enc:
            email_plain = _decrypt_email(email_enc, tenant_id)
            conn.execute(
                text("UPDATE entrada_padron SET email = :e WHERE id = :id"),
                {"e": email_plain, "id": row_id},
            )

    # 3. Drop new columns and index
    op.drop_index("ix_entrada_padron_tenant_email_hash", table_name="entrada_padron")
    op.drop_column("entrada_padron", "email_hash")
    op.drop_column("entrada_padron", "email_enc")

    # 4. Set NOT NULL on email
    op.alter_column("entrada_padron", "email", nullable=False)
