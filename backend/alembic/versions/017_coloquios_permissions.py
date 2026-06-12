"""017: coloquios permissions (C-14).

Adds coloquios:gestionar, coloquios:ver, coloquios:reservar
and assigns them to COORDINADOR, ADMIN, and ALUMNO roles.

Run order:
    alembic upgrade head
    alembic downgrade -1
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op


revision: str = "017_coloquios_permissions"
down_revision: Union[str, None] = "016_evaluaciones"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

COLOQUIOS_GESTIONAR_ID = "00000000-0000-0000-0001-b00000000001"
COLOQUIOS_VER_ID = "00000000-0000-0000-0001-b00000000002"
COLOQUIOS_RESERVAR_ID = "00000000-0000-0000-0001-b00000000003"

COORDINADOR_ID = "00000000-0000-0000-0000-a00000000004"
ADMIN_ID = "00000000-0000-0000-0000-a00000000006"
ALUMNO_ID = "00000000-0000-0000-0000-a00000000002"
GLOBAL_TENANT = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def upgrade() -> None:
    op.execute(f"""
        INSERT INTO permiso (id, tenant_id, modulo, accion, created_at, updated_at, deleted_at)
        VALUES
            ('{COLOQUIOS_GESTIONAR_ID}', '{GLOBAL_TENANT}', 'coloquios', 'gestionar', now(), now(), NULL),
            ('{COLOQUIOS_VER_ID}', '{GLOBAL_TENANT}', 'coloquios', 'ver', now(), now(), NULL),
            ('{COLOQUIOS_RESERVAR_ID}', '{GLOBAL_TENANT}', 'coloquios', 'reservar', now(), now(), NULL)
        ON CONFLICT (tenant_id, modulo, accion) DO NOTHING
    """)

    op.execute(f"""
        INSERT INTO rol_permiso (id, tenant_id, rol_id, permiso_id, created_at)
        VALUES
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{COORDINADOR_ID}', '{COLOQUIOS_GESTIONAR_ID}', now()),
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{ADMIN_ID}', '{COLOQUIOS_GESTIONAR_ID}', now()),
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{COORDINADOR_ID}', '{COLOQUIOS_VER_ID}', now()),
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{ADMIN_ID}', '{COLOQUIOS_VER_ID}', now()),
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{ALUMNO_ID}', '{COLOQUIOS_RESERVAR_ID}', now())
        ON CONFLICT (tenant_id, rol_id, permiso_id) DO NOTHING
    """)


def downgrade() -> None:
    op.execute(f"DELETE FROM rol_permiso WHERE permiso_id IN ('{COLOQUIOS_GESTIONAR_ID}', '{COLOQUIOS_VER_ID}', '{COLOQUIOS_RESERVAR_ID}')")
    op.execute(f"DELETE FROM permiso WHERE id IN ('{COLOQUIOS_GESTIONAR_ID}', '{COLOQUIOS_VER_ID}', '{COLOQUIOS_RESERVAR_ID}')")