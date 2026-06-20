"""027: coloquios:ver + coloquios:reservar para ALUMNO.

ALUMNO necesita coloquios:ver para listar convocatorias disponibles
y coloquios:reservar para crear/ver/cancelar sus reservas.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op


revision: str = "027_alumno_coloquios"
down_revision: Union[str, None] = "026_merge_heads"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

COLOQUIOS_VER_ID = "00000000-0000-0000-0001-b00000000002"
COLOQUIOS_RESERVAR_ID = "00000000-0000-0000-0001-b00000000003"
ALUMNO_ID = "00000000-0000-0000-0000-a00000000001"
GLOBAL_TENANT = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def upgrade() -> None:
    op.execute(f"""
        INSERT INTO rol_permiso (id, tenant_id, rol_id, permiso_id, created_at)
        VALUES
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{ALUMNO_ID}', '{COLOQUIOS_VER_ID}', now()),
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{ALUMNO_ID}', '{COLOQUIOS_RESERVAR_ID}', now())
        ON CONFLICT (tenant_id, rol_id, permiso_id) DO NOTHING
    """)


def downgrade() -> None:
    op.execute(f"""
        DELETE FROM rol_permiso
        WHERE tenant_id = '{GLOBAL_TENANT}'
          AND rol_id = '{ALUMNO_ID}'
          AND permiso_id IN ('{COLOQUIOS_VER_ID}', '{COLOQUIOS_RESERVAR_ID}')
    """)
