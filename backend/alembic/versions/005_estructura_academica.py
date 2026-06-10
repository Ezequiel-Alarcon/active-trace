"""005: estructura_academica — carrera, cohorte, materia (C-06 §1).

Run order:
    alembic upgrade head    # creates tables
    alembic downgrade -1    # drops all three (CASCADE)

Naming convention:
    ix_<tabla>_<cols> (unique for compound), ix_<tabla>_<cols> (non-unique)
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "005_estructura_academica"
down_revision: Union[str, None] = "004_rbac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------- carrera ----------
    op.create_table(
        "carrera",
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
        sa.Column("codigo", sa.String(length=64), nullable=False),
        sa.Column("nombre", sa.String(length=255), nullable=False),
        sa.Column(
            "estado",
            sa.String(length=16),
            nullable=False,
            server_default="Activa",
        ),
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
        "ix_carrera_tenant_codigo", "carrera", ["tenant_id", "codigo"], unique=True
    )
    op.create_index(
        "ix_carrera_tenant_deleted", "carrera", ["tenant_id", "deleted_at"]
    )

    # ---------- cohorte ----------
    op.create_table(
        "cohorte",
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
            "carrera_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("carrera.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("nombre", sa.String(length=128), nullable=False),
        sa.Column("anio", sa.Integer(), nullable=False),
        sa.Column("vig_desde", sa.Date(), nullable=False),
        sa.Column("vig_hasta", sa.Date(), nullable=True),
        sa.Column(
            "estado",
            sa.String(length=16),
            nullable=False,
            server_default="Activa",
        ),
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
        "ix_cohorte_tenant_carrera_nombre",
        "cohorte",
        ["tenant_id", "carrera_id", "nombre"],
        unique=True,
    )
    op.create_index(
        "ix_cohorte_tenant_deleted", "cohorte", ["tenant_id", "deleted_at"]
    )

    # ---------- materia ----------
    op.create_table(
        "materia",
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
        sa.Column("codigo", sa.String(length=64), nullable=False),
        sa.Column("nombre", sa.String(length=255), nullable=False),
        sa.Column(
            "estado",
            sa.String(length=16),
            nullable=False,
            server_default="Activa",
        ),
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
        "ix_materia_tenant_codigo", "materia", ["tenant_id", "codigo"], unique=True
    )
    op.create_index(
        "ix_materia_tenant_deleted", "materia", ["tenant_id", "deleted_at"]
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS materia CASCADE")
    op.execute("DROP TABLE IF EXISTS cohorte CASCADE")
    op.execute("DROP TABLE IF EXISTS carrera CASCADE")
