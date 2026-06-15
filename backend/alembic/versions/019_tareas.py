"""019: add tarea, comentario_tarea tables and tareas:gestionar permission (C-16).

Run order:
    alembic upgrade head
    alembic downgrade -1
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ENUM as pg_ENUM


revision: str = "019_tareas"
down_revision: Union[str, None] = "018_avisos"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ── Permission IDs (from 004_rbac seed) ────────────────────────────────
TAREAS_GESTIONAR_ID = "00000000-0000-0000-0001-a00000000012"

# ── Role IDs (from 004_rbac seed) ───────────────────────────────────────
ALUMNO_ID = "00000000-0000-0000-0000-a00000000001"
TUTOR_ID = "00000000-0000-0000-0000-a00000000002"
PROFESOR_ID = "00000000-0000-0000-0000-a00000000003"
COORDINADOR_ID = "00000000-0000-0000-0000-a00000000004"
NEXO_ID = "00000000-0000-0000-0000-a00000000005"
ADMIN_ID = "00000000-0000-0000-0000-a00000000006"
FINANZAS_ID = "00000000-0000-0000-0000-a00000000007"

GLOBAL_TENANT = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def upgrade() -> None:
    # ── estado_tarea enum ─────────────────────────────────────────────
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE estado_tarea AS ENUM ('Pendiente', 'En progreso', 'Resuelta', 'Cancelada');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # ── tarea table ──────────────────────────────────────────────────
    op.create_table(
        "tarea",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("materia_id", sa.UUID(), nullable=True),
        sa.Column("asignado_a", sa.UUID(), nullable=False),
        sa.Column("asignado_por", sa.UUID(), nullable=False),
        sa.Column("estado", pg_ENUM("Pendiente", "En progreso", "Resuelta", "Cancelada", name="estado_tarea", create_type=False), nullable=False, server_default="Pendiente"),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("contexto_id", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="RESTRICT"),
        sa.Index("ix_tarea_tenant", "tenant_id"),
        sa.Index("ix_tarea_tenant_deleted", "tenant_id", "deleted_at"),
        sa.Index("ix_tarea_asignado_a", "tenant_id", "asignado_a"),
        sa.Index("ix_tarea_estado", "tenant_id", "estado"),
    )

    # ── comentario_tarea table ───────────────────────────────────────────
    op.create_table(
        "comentario_tarea",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tarea_id", sa.UUID(), nullable=False),
        sa.Column("autor_id", sa.UUID(), nullable=False),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tarea_id"], ["tarea.id"], ondelete="CASCADE"),
        sa.Index("ix_comentario_tarea_tenant", "tenant_id"),
        sa.Index("ix_comentario_tarea_tenant_deleted", "tenant_id", "deleted_at"),
        sa.Index("ix_comentario_tarea_tarea", "tenant_id", "tarea_id"),
    )

    # ── Permission seeds ─────────────────────────────────────────────
    op.execute(f"""
        INSERT INTO permiso (id, tenant_id, modulo, accion, created_at, updated_at, deleted_at)
        VALUES
            ('{TAREAS_GESTIONAR_ID}', '{GLOBAL_TENANT}', 'tareas', 'gestionar', now(), now(), NULL)
        ON CONFLICT (tenant_id, modulo, accion) DO NOTHING
    """)

    # tareas:gestionar → PROFESOR, COORDINADOR, ADMIN
    op.execute(f"""
        INSERT INTO rol_permiso (id, tenant_id, rol_id, permiso_id, created_at)
        VALUES
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{PROFESOR_ID}', '{TAREAS_GESTIONAR_ID}', now()),
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{COORDINADOR_ID}', '{TAREAS_GESTIONAR_ID}', now()),
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{ADMIN_ID}', '{TAREAS_GESTIONAR_ID}', now())
        ON CONFLICT (tenant_id, rol_id, permiso_id) DO NOTHING
    """)


def downgrade() -> None:
    op.execute(
        f"DELETE FROM rol_permiso WHERE permiso_id IN ('{TAREAS_GESTIONAR_ID}')"
    )
    op.execute(
        f"DELETE FROM permiso WHERE id IN ('{TAREAS_GESTIONAR_ID}')"
    )
    op.drop_table("comentario_tarea")
    op.drop_table("tarea")
    op.execute("DROP TYPE IF EXISTS estado_tarea")
