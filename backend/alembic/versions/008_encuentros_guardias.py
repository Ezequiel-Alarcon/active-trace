"""008: encuentros_guardias — slot_encuentro, instancia_encuentro, guardia (C-18).

Run order:
    alembic upgrade head    # creates tables
    alembic downgrade -1    # drops all three (CASCADE)
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "008_encuentros_guardias"
down_revision: Union[str, None] = "007_programas_fechas"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------- slot_encuentro ----------
    op.create_table(
        "slot_encuentro",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenant.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("materia.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "cohorte_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cohorte.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("titulo", sa.String(length=255), nullable=False),
        sa.Column("dia_semana", sa.Integer(), nullable=False),
        sa.Column("hora_inicio", sa.Time(), nullable=False),
        sa.Column("hora_fin", sa.Time(), nullable=False),
        sa.Column("fecha_inicio", sa.Date(), nullable=False),
        sa.Column("cant_semanas", sa.Integer(), nullable=False),
        sa.Column("meet_url", sa.String(length=512), nullable=True),
        sa.Column("video_url", sa.String(length=512), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_slot_encuentro_tenant_materia_cohorte",
        "slot_encuentro",
        ["tenant_id", "materia_id", "cohorte_id"],
    )
    op.create_index(
        "ix_slot_encuentro_tenant_deleted",
        "slot_encuentro",
        ["tenant_id", "deleted_at"],
    )

    # ---------- instancia_encuentro ----------
    op.create_table(
        "instancia_encuentro",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenant.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "slot_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("slot_encuentro.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("materia.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "cohorte_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cohorte.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("hora_inicio", sa.Time(), nullable=False),
        sa.Column("hora_fin", sa.Time(), nullable=False),
        sa.Column("titulo", sa.String(length=255), nullable=False),
        sa.Column("estado", sa.String(length=16), nullable=False, server_default="Programado"),
        sa.Column("meet_url", sa.String(length=512), nullable=True),
        sa.Column("video_url", sa.String(length=512), nullable=True),
        sa.Column("comentario", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_instancia_encuentro_tenant_materia_cohorte",
        "instancia_encuentro",
        ["tenant_id", "materia_id", "cohorte_id"],
    )
    op.create_index(
        "ix_instancia_encuentro_tenant_slot",
        "instancia_encuentro",
        ["tenant_id", "slot_id"],
    )
    op.create_index(
        "ix_instancia_encuentro_tenant_deleted",
        "instancia_encuentro",
        ["tenant_id", "deleted_at"],
    )

    # ---------- guardia ----------
    op.create_table(
        "guardia",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenant.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "tutor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuario.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("materia.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "cohorte_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cohorte.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("hora_inicio", sa.Time(), nullable=False),
        sa.Column("hora_fin", sa.Time(), nullable=False),
        sa.Column("titulo", sa.String(length=255), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_guardia_tenant_tutor",
        "guardia",
        ["tenant_id", "tutor_id"],
    )
    op.create_index(
        "ix_guardia_tenant_materia_cohorte",
        "guardia",
        ["tenant_id", "materia_id", "cohorte_id"],
    )
    op.create_index(
        "ix_guardia_tenant_deleted",
        "guardia",
        ["tenant_id", "deleted_at"],
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS guardia CASCADE")
    op.execute("DROP TABLE IF EXISTS instancia_encuentro CASCADE")
    op.execute("DROP TABLE IF EXISTS slot_encuentro CASCADE")
