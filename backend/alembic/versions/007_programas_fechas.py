"""007: programas_fechas — programa_materia, fecha_academica (C-17 §1).

Run order:
    alembic upgrade head    # creates tables
    alembic downgrade -1    # drops both (CASCADE)

Naming convention:
    ix_<tabla>_<cols> (unique for compound), ix_<tabla>_<cols> (non-unique)

Note: down_revision targets 005_estructura_academica as 006_usuarios_asignaciones
(C-07) does not exist yet. Adjust to 006_usuarios_asignaciones when C-07 migrates.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "007_programas_fechas"
down_revision: Union[str, None] = "005_audit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------- programa_materia ----------
    op.create_table(
        "programa_materia",
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
            "carrera_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("carrera.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "cohorte_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cohorte.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("titulo", sa.String(length=255), nullable=False),
        sa.Column("referencia_archivo", sa.String(length=512), nullable=True),
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
        "ix_programa_materia_tenant_materia_carrera_cohorte",
        "programa_materia",
        ["tenant_id", "materia_id", "carrera_id", "cohorte_id"],
        unique=True,
    )
    op.create_index(
        "ix_programa_materia_tenant_deleted",
        "programa_materia",
        ["tenant_id", "deleted_at"],
    )

    # ---------- fecha_academica ----------
    op.create_table(
        "fecha_academica",
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
        sa.Column("tipo", sa.String(length=16), nullable=False),
        sa.Column("numero_instancia", sa.Integer(), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("titulo", sa.String(length=255), nullable=True),
        sa.Column("descripcion", sa.Text(), nullable=True),
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
        "ix_fecha_academica_tenant_materia_cohorte_tipo_num",
        "fecha_academica",
        ["tenant_id", "materia_id", "cohorte_id", "tipo", "numero_instancia"],
        unique=True,
    )
    op.create_index(
        "ix_fecha_academica_tenant_deleted",
        "fecha_academica",
        ["tenant_id", "deleted_at"],
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS fecha_academica CASCADE")
    op.execute("DROP TABLE IF EXISTS programa_materia CASCADE")
