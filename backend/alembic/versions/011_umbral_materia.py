"""011: umbral_materia table (C-10).

Run order:
    alembic upgrade head
    alembic downgrade -1
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "011_umbral_materia"
down_revision: Union[str, None] = "010_calificaciones"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "umbral_materia",
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
            nullable=False,
        ),
        sa.Column(
            "asignacion_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "umbral_pct",
            sa.Integer(),
            nullable=False,
            default=60,
        ),
        sa.Column(
            "conjunto_aprobado",
            postgresql.JSONB,
            nullable=True,
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
        "ix_umbral_materia_tenant",
        "umbral_materia",
        ["tenant_id"],
    )
    op.create_index(
        "ix_umbral_materia_materia",
        "umbral_materia",
        ["materia_id"],
    )
    op.create_index(
        "ix_umbral_materia_asignacion",
        "umbral_materia",
        ["asignacion_id"],
    )
    op.create_index(
        "ix_umbral_materia_tenant_deleted",
        "umbral_materia",
        ["tenant_id", "deleted_at"],
    )
    op.create_index(
        "ix_umbral_materia_materia_asignacion_deleted",
        "umbral_materia",
        ["materia_id", "asignacion_id", "deleted_at"],
        unique=True,
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS umbral_materia CASCADE")