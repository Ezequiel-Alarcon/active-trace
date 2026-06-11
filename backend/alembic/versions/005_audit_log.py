"""005: audit_log — E-AUD append-only audit log (C-05 §1).

Run order:
    alembic upgrade head    # creates audit_log table + indexes
    alembic downgrade -1    # drops audit_log (CASCADE)

Naming convention:
    pk_<table>, ix_<table>_<cols>, ux_<table>_<col>
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "005_audit"
down_revision: Union[str, None] = "004_rbac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_log",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("fecha_hora", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("actor_id", sa.UUID(), nullable=False),
        sa.Column("impersonado_id", sa.UUID(), nullable=True),
        sa.Column("materia_id", sa.UUID(), nullable=True),
        sa.Column("accion", sa.String(64), nullable=False),
        sa.Column("detalle", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("filas_afectadas", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("ip", sa.String(64), nullable=False),
        sa.Column("user_agent", sa.String(512), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_log_tenant_fecha", "audit_log", ["tenant_id", "fecha_hora"], unique=False)
    op.create_index("ix_audit_log_actor", "audit_log", ["actor_id"], unique=False)
    op.create_index("ix_audit_log_accion", "audit_log", ["accion"], unique=False)
    op.create_index("ix_audit_log_impersonado", "audit_log", ["impersonado_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_audit_log_impersonado", table_name="audit_log")
    op.drop_index("ix_audit_log_accion", table_name="audit_log")
    op.drop_index("ix_audit_log_actor", table_name="audit_log")
    op.drop_index("ix_audit_log_tenant_fecha", table_name="audit_log")
    op.drop_table("audit_log")


# Import for JSONB type
from sqlalchemy.dialects import postgresql  # noqa: E402, F401