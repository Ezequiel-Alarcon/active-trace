"""024: add mensajes:enviar and mensajes:ver permissions (C-28).

Adds mensajes:enviar and mensajes:ver to the permission catalogue and
assigns them to all roles (ALUMNO, TUTOR, PROFESOR, COORDINADOR,
NEXO, ADMIN, FINANZAS) since messaging is available to all authenticated
users.

Run order:
    alembic upgrade head
    alembic downgrade -1
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op


revision: str = "024_mensajes_permissions"
down_revision: Union[str, None] = "023_liquidaciones_honorarios"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Permission IDs (continuing from 00000000001-a00000000029 used in 022)
MENSAJES_ENVIAR_ID = "00000000-0000-0000-0001-a0000000002a"
MENSAJES_VER_ID = "00000000-0000-0000-0001-a0000000002b"

# Rol IDs (from 004 seed)
ALUMNO_ID = "00000000-0000-0000-0000-a00000000001"
TUTOR_ID = "00000000-0000-0000-0000-a00000000002"
PROFESOR_ID = "00000000-0000-0000-0000-a00000000003"
COORDINADOR_ID = "00000000-0000-0000-0000-a00000000004"
NEXO_ID = "00000000-0000-0000-0000-a00000000005"
ADMIN_ID = "00000000-0000-0000-0000-a00000000006"
FINANZAS_ID = "00000000-0000-0000-0000-a00000000007"
GLOBAL_TENANT = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def upgrade() -> None:
    # Insert mensajes:enviar permission
    op.execute(f"""
        INSERT INTO permiso (id, tenant_id, modulo, accion, created_at, updated_at, deleted_at)
        VALUES
            ('{MENSAJES_ENVIAR_ID}', '{GLOBAL_TENANT}', 'mensajes', 'enviar', now(), now(), NULL),
            ('{MENSAJES_VER_ID}', '{GLOBAL_TENANT}', 'mensajes', 'ver', now(), now(), NULL)
        ON CONFLICT (tenant_id, modulo, accion) DO NOTHING
    """)

    # Assign mensajes:enviar to all roles
    op.execute(f"""
        INSERT INTO rol_permiso (id, tenant_id, rol_id, permiso_id, created_at)
        VALUES
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{ALUMNO_ID}', '{MENSAJES_ENVIAR_ID}', now()),
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{TUTOR_ID}', '{MENSAJES_ENVIAR_ID}', now()),
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{PROFESOR_ID}', '{MENSAJES_ENVIAR_ID}', now()),
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{COORDINADOR_ID}', '{MENSAJES_ENVIAR_ID}', now()),
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{NEXO_ID}', '{MENSAJES_ENVIAR_ID}', now()),
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{ADMIN_ID}', '{MENSAJES_ENVIAR_ID}', now()),
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{FINANZAS_ID}', '{MENSAJES_ENVIAR_ID}', now())
        ON CONFLICT (tenant_id, rol_id, permiso_id) DO NOTHING
    """)

    # Assign mensajes:ver to all roles
    op.execute(f"""
        INSERT INTO rol_permiso (id, tenant_id, rol_id, permiso_id, created_at)
        VALUES
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{ALUMNO_ID}', '{MENSAJES_VER_ID}', now()),
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{TUTOR_ID}', '{MENSAJES_VER_ID}', now()),
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{PROFESOR_ID}', '{MENSAJES_VER_ID}', now()),
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{COORDINADOR_ID}', '{MENSAJES_VER_ID}', now()),
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{NEXO_ID}', '{MENSAJES_VER_ID}', now()),
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{ADMIN_ID}', '{MENSAJES_VER_ID}', now()),
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{FINANZAS_ID}', '{MENSAJES_VER_ID}', now())
        ON CONFLICT (tenant_id, rol_id, permiso_id) DO NOTHING
    """)


def downgrade() -> None:
    op.execute(f"DELETE FROM rol_permiso WHERE permiso_id IN ('{MENSAJES_ENVIAR_ID}', '{MENSAJES_VER_ID}')")
    op.execute(f"DELETE FROM permiso WHERE id IN ('{MENSAJES_ENVIAR_ID}', '{MENSAJES_VER_ID}')")
