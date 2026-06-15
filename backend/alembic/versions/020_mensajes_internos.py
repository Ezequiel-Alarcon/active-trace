"""020: add mensaje_interno table (C-20).

Run order:
    alembic upgrade head
    alembic downgrade -1
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "020_mensajes_internos"
down_revision: Union[str, None] = "019_tareas"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mensaje_interno",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("asunto", sa.Text(), nullable=False),
        sa.Column("cuerpo", sa.Text(), nullable=False),
        sa.Column("remitente_id", sa.UUID(), nullable=False),
        sa.Column("destinatario_id", sa.UUID(), nullable=False),
        sa.Column("hilo_id", sa.UUID(), nullable=False),
        sa.Column("padre_id", sa.UUID(), nullable=True),
        sa.Column("leido_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["remitente_id"], ["usuario.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["destinatario_id"], ["usuario.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["padre_id"], ["mensaje_interno.id"], ondelete="SET NULL"),
        sa.Index("ix_mensaje_interno_tenant", "tenant_id"),
        sa.Index("ix_mensaje_interno_tenant_deleted", "tenant_id", "deleted_at"),
        sa.Index("ix_mensaje_interno_remitente", "tenant_id", "remitente_id"),
        sa.Index("ix_mensaje_interno_destinatario", "tenant_id", "destinatario_id"),
        sa.Index("ix_mensaje_interno_hilo", "tenant_id", "hilo_id"),
    )


def downgrade() -> None:
    op.drop_table("mensaje_interno")
