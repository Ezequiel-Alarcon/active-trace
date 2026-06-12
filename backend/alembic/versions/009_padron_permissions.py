"""009: padron permissions (C-09).

Adds padron:importar and padron:ver to the permission catalogue
and assigns them to PROFESOR, COORDINADOR, ADMIN roles.

Run order:
    alembic upgrade head
    alembic downgrade -1
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "009_padron_permissions"
down_revision: Union[str, None] = "008_encuentros_guardias"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Permission IDs (continuing from 00023 used in 004)
PADRON_IMPORTAR_ID = "00000000-0000-0000-0001-a00000000024"
PADRON_VER_ID = "00000000-0000-0000-0001-a00000000025"

# Rol IDs (from 004 seed)
PROFESOR_ID = "00000000-0000-0000-0000-a00000000003"
COORDINADOR_ID = "00000000-0000-0000-0000-a00000000004"
ADMIN_ID = "00000000-0000-0000-0000-a00000000006"
GLOBAL_TENANT = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def upgrade() -> None:
    # Insert padron permissions
    op.execute(f"""
        INSERT INTO permiso (id, tenant_id, modulo, accion, created_at, updated_at, deleted_at)
        VALUES
            ('{PADRON_IMPORTAR_ID}', '{GLOBAL_TENANT}', 'padron', 'importar', now(), now(), NULL),
            ('{PADRON_VER_ID}', '{GLOBAL_TENANT}', 'padron', 'ver', now(), now(), NULL)
        ON CONFLICT (tenant_id, modulo, accion) DO NOTHING
    """)

    # Assign padron:importar to PROFESOR, COORDINADOR, ADMIN
    op.execute(f"""
        INSERT INTO rol_permiso (id, tenant_id, rol_id, permiso_id, created_at)
        VALUES
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{PROFESOR_ID}', '{PADRON_IMPORTAR_ID}', now()),
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{COORDINADOR_ID}', '{PADRON_IMPORTAR_ID}', now()),
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{ADMIN_ID}', '{PADRON_IMPORTAR_ID}', now())
        ON CONFLICT (tenant_id, rol_id, permiso_id) DO NOTHING
    """)

    # Assign padron:ver to PROFESOR, COORDINADOR, ADMIN
    op.execute(f"""
        INSERT INTO rol_permiso (id, tenant_id, rol_id, permiso_id, created_at)
        VALUES
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{PROFESOR_ID}', '{PADRON_VER_ID}', now()),
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{COORDINADOR_ID}', '{PADRON_VER_ID}', now()),
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{ADMIN_ID}', '{PADRON_VER_ID}', now())
        ON CONFLICT (tenant_id, rol_id, permiso_id) DO NOTHING
    """)


def downgrade() -> None:
    op.execute(f"DELETE FROM rol_permiso WHERE permiso_id IN ('{PADRON_IMPORTAR_ID}', '{PADRON_VER_ID}')")
    op.execute(f"DELETE FROM permiso WHERE id IN ('{PADRON_IMPORTAR_ID}', '{PADRON_VER_ID}')")