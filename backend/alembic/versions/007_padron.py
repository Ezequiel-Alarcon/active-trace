"""007: version_padron, entrada_padron (C-09).

Run order:
    alembic upgrade head    # creates tables
    alembic downgrade -1    # drops both (CASCADE)
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "007_padron"
down_revision: Union[str, None] = "008_encuentros_guardias"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "version_padron",
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
            "cohorte_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "cargado_por",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "cargado_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("activa", sa.Boolean(), nullable=False, default=False),
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
        "ix_version_padron_tenant",
        "version_padron",
        ["tenant_id"],
    )
    op.create_index(
        "ix_version_padron_materia_cohorte_activa",
        "version_padron",
        ["materia_id", "cohorte_id", "activa"],
    )
    op.create_index(
        "ix_version_padron_tenant_deleted",
        "version_padron",
        ["tenant_id", "deleted_at"],
    )

    op.create_table(
        "entrada_padron",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("version_padron.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenant.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("nombre", sa.String(length=128), nullable=False),
        sa.Column("apellidos", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=2048), nullable=False),
        sa.Column("comision", sa.String(length=64), nullable=True),
        sa.Column("regional", sa.String(length=128), nullable=True),
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
        "ix_entrada_padron_tenant",
        "entrada_padron",
        ["tenant_id"],
    )
    op.create_index(
        "ix_entrada_padron_version",
        "entrada_padron",
        ["version_id"],
    )
    op.create_index(
        "ix_entrada_padron_usuario",
        "entrada_padron",
        ["usuario_id"],
    )
    op.create_index(
        "ix_entrada_padron_tenant_deleted",
        "entrada_padron",
        ["tenant_id", "deleted_at"],
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS entrada_padron CASCADE")
    op.execute("DROP TABLE IF EXISTS version_padron CASCADE")