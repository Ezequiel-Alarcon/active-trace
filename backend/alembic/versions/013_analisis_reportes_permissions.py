"""013: analisis y reportes permissions (C-11).

Agrega permisos analisis:ver, reportes:ver, reportes:exportar
y los asigna a los roles correspondientes.

Run order:
    alembic upgrade head
    alembic downgrade -1
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op


revision: str = "013_analisis_reportes_permissions"
down_revision: Union[str, None] = "012_seed_umbral_materia"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ANALISIS_VER_ID = "00000000-0000-0000-0001-a00000000026"
REPORTES_VER_ID = "00000000-0000-0000-0001-a00000000027"
REPORTES_EXPORTAR_ID = "00000000-0000-0000-0001-a00000000028"

PROFESOR_ID = "00000000-0000-0000-0000-a00000000003"
TUTOR_ID = "00000000-0000-0000-0000-a00000000002"
COORDINADOR_ID = "00000000-0000-0000-0000-a00000000004"
ADMIN_ID = "00000000-0000-0000-0000-a00000000006"
GLOBAL_TENANT = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def upgrade() -> None:
    op.execute(f"""
        INSERT INTO permiso (id, tenant_id, modulo, accion, created_at, updated_at, deleted_at)
        VALUES
            ('{ANALISIS_VER_ID}', '{GLOBAL_TENANT}', 'analisis', 'ver', now(), now(), NULL),
            ('{REPORTES_VER_ID}', '{GLOBAL_TENANT}', 'reportes', 'ver', now(), now(), NULL),
            ('{REPORTES_EXPORTAR_ID}', '{GLOBAL_TENANT}', 'reportes', 'exportar', now(), now(), NULL)
        ON CONFLICT (tenant_id, modulo, accion) DO NOTHING
    """)

    op.execute(f"""
        INSERT INTO rol_permiso (id, tenant_id, rol_id, permiso_id, created_at)
        VALUES
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{PROFESOR_ID}', '{ANALISIS_VER_ID}', now()),
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{TUTOR_ID}', '{ANALISIS_VER_ID}', now())
        ON CONFLICT (tenant_id, rol_id, permiso_id) DO NOTHING
    """)

    op.execute(f"""
        INSERT INTO rol_permiso (id, tenant_id, rol_id, permiso_id, created_at)
        VALUES
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{COORDINADOR_ID}', '{REPORTES_VER_ID}', now()),
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{ADMIN_ID}', '{REPORTES_VER_ID}', now()),
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{COORDINADOR_ID}', '{REPORTES_EXPORTAR_ID}', now()),
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{ADMIN_ID}', '{REPORTES_EXPORTAR_ID}', now())
        ON CONFLICT (tenant_id, rol_id, permiso_id) DO NOTHING
    """)


def downgrade() -> None:
    op.execute(f"DELETE FROM rol_permiso WHERE permiso_id IN ('{ANALISIS_VER_ID}', '{REPORTES_VER_ID}', '{REPORTES_EXPORTAR_ID}')")
    op.execute(f"DELETE FROM permiso WHERE id IN ('{ANALISIS_VER_ID}', '{REPORTES_VER_ID}', '{REPORTES_EXPORTAR_ID}')")