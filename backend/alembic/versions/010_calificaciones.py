"""010: calificacion table (C-10).

Run order:
    alembic upgrade head
    alembic downgrade -1
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "010_calificaciones"
down_revision: Union[str, None] = "009_padron_permissions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "calificacion",
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
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "asignacion_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "version_padron_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "nota",
            postgresql.JSONB,
            nullable=True,
        ),
        sa.Column(
            "origen",
            sa.String(length=16),
            nullable=False,
        ),
        sa.Column(
            "import_batch_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
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
        "ix_calificacion_tenant",
        "calificacion",
        ["tenant_id"],
    )
    op.create_index(
        "ix_calificacion_materia",
        "calificacion",
        ["materia_id"],
    )
    op.create_index(
        "ix_calificacion_usuario",
        "calificacion",
        ["usuario_id"],
    )
    op.create_index(
        "ix_calificacion_asignacion",
        "calificacion",
        ["asignacion_id"],
    )
    op.create_index(
        "ix_calificacion_tenant_deleted",
        "calificacion",
        ["tenant_id", "deleted_at"],
    )
    op.create_index(
        "ix_calificacion_import_batch",
        "calificacion",
        ["import_batch_id"],
    )
    op.create_index(
        "ix_calificacion_materia_usuario_asignacion_deleted",
        "calificacion",
        ["materia_id", "usuario_id", "asignacion_id", "deleted_at"],
        unique=True,
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS calificacion CASCADE")