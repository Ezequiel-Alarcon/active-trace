"""025: backfill comunicacion.destinatario_enc (C-29).

Populates the encrypted `destinatario_enc` column for all existing
Comunicacion records that have a plaintext `destinatario` but no
`destinatario_enc`.

This is NOT a schema migration — the columns (destinatario_enc,
destinatario_hash) were added by a prior migration. This migration
exists solely to backfill those columns for pre-existing data.

IMPORTANT: This migration is idempotent and re-run safe.
The WHERE clause ensures we only touch records that still need backfill.

Run order:
    alembic upgrade head
    # to rollback (no-op for data, just schema-keep):
    alembic downgrade -1
"""

from __future__ import annotations

from uuid import UUID
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "025_comunicacion_backfill_destinatario_enc"
down_revision: Union[str, None] = "024_mensajes_permissions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Backfill destinatario_enc for all records that have plaintext destinatario.

    Iterates in batches to avoid long table locks.
    Uses the actual app encryption and hashing functions for correctness.
    """
    # Import here to avoid circular imports at module level.
    from app.core.security.crypto import encrypt
    from app.core.security.hashing import hash_email_for_search

    # We need a DB connection to iterate rows.
    connection = op.get_bind()

    # Fetch records needing backfill in batches.
    batch_size = 500
    offset = 0

    while True:
        result = connection.execute(
            sa.text("""
                SELECT id, tenant_id, destinatario
                FROM comunicacion
                WHERE destinatario_enc IS NULL
                   OR destinatario_enc = ''
                   OR destinatario_hash IS NULL
                   OR destinatario_hash = ''
                ORDER BY id
                LIMIT :batch_size OFFSET :offset
            """),
            {"batch_size": batch_size, "offset": offset},
        )
        rows = result.fetchall()
        if not rows:
            break

        for row in rows:
            record_id = row[0]
            tenant_id = row[1]
            plain_email = row[2]

            if not plain_email:
                continue

            plain_lower = plain_email.strip().lower()
            email_hash = hash_email_for_search(plain_lower, UUID(str(tenant_id)))
            try:
                email_enc = encrypt(
                    plain_lower,
                    tenant_id=UUID(str(tenant_id)),
                    aad_suffix="comunicacion.destinatario",
                )
            except Exception:
                # If encryption fails (e.g. missing key), skip — record stays as-is.
                continue

            connection.execute(
                sa.text("""
                    UPDATE comunicacion
                    SET destinatario_hash = :hash,
                        destinatario_enc = :enc
                    WHERE id = :id
                """),
                {"hash": email_hash, "enc": email_enc, "id": record_id},
            )

        offset += batch_size


def downgrade() -> None:
    # No-op: backfill only writes to existing columns; no schema changes.
    pass
