"""019: add tarea, comentario_tarea tables and tareas:gestionar permission (C-16).

Run order:
    alembic upgrade head
    alembic downgrade -1
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op


revision: str = "019_tareas"
down_revision: Union[str, None] = "018_avisos"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ── Permission IDs ─────────────────────────────────────────────────────
TAREAS_GESTIONAR_ID = "00000000-0000-0000-0001-d00000000001"

# ── Role IDs ────────────────────────────────────────────────────────────
ALUMNO_ID = "00000000-0000-0000-0000-a00000000002"
TUTOR_ID = "00000000-0000-0000-0000-a00000000003"
COORDINADOR_ID = "00000000-0000-0000-0000-a00000000004"
NEXO_ID = "00000000-0000-0000-0000-a00000000005"
ADMIN_ID = "00000000-0000-0000-0000-a00000000006"
FINANZAS_ID = "00000000-0000-0000-0000-a00000000007"
PROFESOR_ID = "00000000-0000-0000-0000-a00000000008"

GLOBAL_TENANT = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def upgrade() -> None:
    # ── estado_tarea enum ─────────────────────────────────────────────
    op.execute("CREATE TYPE estado_tarea AS ENUM ('Pendiente', 'En progreso', 'Resuelta', 'Cancelada')")

    # ── tarea table ──────────────────────────────────────────────────
    op.create_table(
        "tarea",
        op.Column("id", op.UUID(), primary_key=True),
        op.Column("tenant_id", op.UUID(), nullable=False),
        op.Column("created_at", op.DateTime(timezone=True), nullable=False, server_default=op.text("now()")),
        op.Column("updated_at", op.DateTime(timezone=True), nullable=False, server_default=op.text("now()")),
        op.Column("deleted_at", op.DateTime(timezone=True), nullable=True),
        op.Column("materia_id", op.UUID(), nullable=True),
        op.Column("asignado_a", op.UUID(), nullable=False),
        op.Column("asignado_por", op.UUID(), nullable=False),
        op.Column("estado", op.Enum("Pendiente", "En progreso", "Resuelta", "Cancelada", name="estado_tarea", create_type=False), nullable=False, server_default="Pendiente"),
        op.Column("descripcion", op.Text(), nullable=False),
        op.Column("contexto_id", op.UUID(), nullable=True),
        op.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="RESTRICT"),
        op.Index("ix_tarea_tenant", "tenant_id"),
        op.Index("ix_tarea_tenant_deleted", "tenant_id", "deleted_at"),
        op.Index("ix_tarea_asignado_a", "tenant_id", "asignado_a"),
        op.Index("ix_tarea_estado", "tenant_id", "estado"),
    )

    # ── comentario_tarea table ───────────────────────────────────────────
    op.create_table(
        "comentario_tarea",
        op.Column("id", op.UUID(), primary_key=True),
        op.Column("tenant_id", op.UUID(), nullable=False),
        op.Column("created_at", op.DateTime(timezone=True), nullable=False, server_default=op.text("now()")),
        op.Column("updated_at", op.DateTime(timezone=True), nullable=False, server_default=op.text("now()")),
        op.Column("deleted_at", op.DateTime(timezone=True), nullable=True),
        op.Column("tarea_id", op.UUID(), nullable=False),
        op.Column("autor_id", op.UUID(), nullable=False),
        op.Column("texto", op.Text(), nullable=False),
        op.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="RESTRICT"),
        op.ForeignKeyConstraint(["tarea_id"], ["tarea.id"], ondelete="CASCADE"),
        op.Index("ix_comentario_tarea_tenant", "tenant_id"),
        op.Index("ix_comentario_tarea_tenant_deleted", "tenant_id", "deleted_at"),
        op.Index("ix_comentario_tarea_tarea", "tenant_id", "tarea_id"),
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
