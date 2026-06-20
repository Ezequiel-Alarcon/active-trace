"""019: coloquios:ver for PROFESOR (read-only access).

Assigns the existing coloquios:ver permission (created in 017) to PROFESOR.

Run order:
    alembic upgrade head
    alembic downgrade -1
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op


revision: str = "019_profesor_coloquios_ver"
down_revision: Union[str, None] = "018_profesor_equipos_permission"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

COLOQUIOS_VER_ID = "00000000-0000-0000-0001-b00000000002"
PROFESOR_ID = "00000000-0000-0000-0000-a00000000003"
GLOBAL_TENANT = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def upgrade() -> None:
    op.execute(f"""
        INSERT INTO rol_permiso (id, tenant_id, rol_id, permiso_id, created_at)
        VALUES (gen_random_uuid(), '{GLOBAL_TENANT}', '{PROFESOR_ID}', '{COLOQUIOS_VER_ID}', now())
        ON CONFLICT (tenant_id, rol_id, permiso_id) DO NOTHING
    """)


def downgrade() -> None:
    op.execute(f"""
        DELETE FROM rol_permiso
        WHERE tenant_id = '{GLOBAL_TENANT}'
          AND rol_id = '{PROFESOR_ID}'
          AND permiso_id = '{COLOQUIOS_VER_ID}'
    """)
