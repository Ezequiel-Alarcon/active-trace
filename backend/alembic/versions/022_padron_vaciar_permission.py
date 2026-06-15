"""022: add padron:vaciar permission (C-09).

Adds padron:vaciar to the permission catalogue and assigns it to
PROFESOR, COORDINADOR, and ADMIN roles.

The endpoint was previously protected (incorrectly) by padron:importar —
this migration creates the dedicated permission required by D3.

Run order:
    alembic upgrade head
    alembic downgrade -1
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op


revision: str = "022_padron_vaciar_permission"
down_revision: Union[str, None] = "021_padron_email_cifrado"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Permission ID (continuing from 00025 used in 009_padron_permissions.py)
PADRON_VACIAR_ID = "00000000-0000-0000-0001-a00000000029"

# Rol IDs (from 004 seed)
PROFESOR_ID = "00000000-0000-0000-0000-a00000000003"
COORDINADOR_ID = "00000000-0000-0000-0000-a00000000004"
ADMIN_ID = "00000000-0000-0000-0000-a00000000006"
GLOBAL_TENANT = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def upgrade() -> None:
    # Insert padron:vaciar permission
    op.execute(f"""
        INSERT INTO permiso (id, tenant_id, modulo, accion, created_at, updated_at, deleted_at)
        VALUES
            ('{PADRON_VACIAR_ID}', '{GLOBAL_TENANT}', 'padron', 'vaciar', now(), now(), NULL)
        ON CONFLICT (tenant_id, modulo, accion) DO NOTHING
    """)

    # Assign padron:vaciar to PROFESOR, COORDINADOR, ADMIN
    op.execute(f"""
        INSERT INTO rol_permiso (id, tenant_id, rol_id, permiso_id, created_at)
        VALUES
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{PROFESOR_ID}', '{PADRON_VACIAR_ID}', now()),
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{COORDINADOR_ID}', '{PADRON_VACIAR_ID}', now()),
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{ADMIN_ID}', '{PADRON_VACIAR_ID}', now())
        ON CONFLICT (tenant_id, rol_id, permiso_id) DO NOTHING
    """)


def downgrade() -> None:
    op.execute(f"DELETE FROM rol_permiso WHERE permiso_id = '{PADRON_VACIAR_ID}'")
    op.execute(f"DELETE FROM permiso WHERE id = '{PADRON_VACIAR_ID}'")
