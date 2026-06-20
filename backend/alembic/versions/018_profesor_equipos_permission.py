"""018: equipos:ver permission for PROFESOR (demo).

Adds equipos:ver permission and assigns it to PROFESOR so
the /api/equipos/mis-equipos endpoint is accessible from the
PROFESOR frontend screen without requiring equipos:asignar.

Run order:
    alembic upgrade head
    alembic downgrade -1
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op


revision: str = "018_profesor_equipos_permission"
down_revision: Union[str, None] = "017_coloquios_permissions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EQUIPOS_VER_ID = "00000000-0000-0000-0001-b00000000010"
PROFESOR_ID = "00000000-0000-0000-0000-a00000000003"
TUTOR_ID = "00000000-0000-0000-0000-a00000000002"
GLOBAL_TENANT = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def upgrade() -> None:
    op.execute(f"""
        INSERT INTO permiso (id, tenant_id, modulo, accion, created_at, updated_at, deleted_at)
        VALUES ('{EQUIPOS_VER_ID}', '{GLOBAL_TENANT}', 'equipos', 'ver', now(), now(), NULL)
        ON CONFLICT (tenant_id, modulo, accion) DO NOTHING
    """)

    op.execute(f"""
        INSERT INTO rol_permiso (id, tenant_id, rol_id, permiso_id, created_at)
        VALUES
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{PROFESOR_ID}', '{EQUIPOS_VER_ID}', now()),
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{TUTOR_ID}',    '{EQUIPOS_VER_ID}', now())
        ON CONFLICT (tenant_id, rol_id, permiso_id) DO NOTHING
    """)


def downgrade() -> None:
    op.execute(f"DELETE FROM rol_permiso WHERE permiso_id = '{EQUIPOS_VER_ID}'")
    op.execute(f"DELETE FROM permiso WHERE id = '{EQUIPOS_VER_ID}'")
