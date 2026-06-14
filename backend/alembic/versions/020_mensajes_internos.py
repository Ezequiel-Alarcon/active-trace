"""020: add mensaje_interno table (C-20).

Run order:
    alembic upgrade head
    alembic downgrade -1
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op


revision: str = "020_mensajes_internos"
down_revision: Union[str, None] = "019_tareas"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mensaje_interno",
        op.Column("id", op.UUID(), primary_key=True),
        op.Column("tenant_id", op.UUID(), nullable=False),
        op.Column("created_at", op.DateTime(timezone=True), nullable=False, server_default=op.text("now()")),
        op.Column("updated_at", op.DateTime(timezone=True), nullable=False, server_default=op.text("now()")),
        op.Column("deleted_at", op.DateTime(timezone=True), nullable=True),
        op.Column("asunto", op.Text(), nullable=False),
        op.Column("cuerpo", op.Text(), nullable=False),
        op.Column("remitente_id", op.UUID(), nullable=False),
        op.Column("destinatario_id", op.UUID(), nullable=False),
        op.Column("hilo_id", op.UUID(), nullable=False),
        op.Column("padre_id", op.UUID(), nullable=True),
        op.Column("leido_at", op.DateTime(timezone=True), nullable=True),
        op.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="RESTRICT"),
        op.ForeignKeyConstraint(["remitente_id"], ["usuario.id"], ondelete="RESTRICT"),
        op.ForeignKeyConstraint(["destinatario_id"], ["usuario.id"], ondelete="RESTRICT"),
        op.ForeignKeyConstraint(["padre_id"], ["mensaje_interno.id"], ondelete="SET NULL"),
        op.Index("ix_mensaje_interno_tenant", "tenant_id"),
        op.Index("ix_mensaje_interno_tenant_deleted", "tenant_id", "deleted_at"),
        op.Index("ix_mensaje_interno_remitente", "tenant_id", "remitente_id"),
        op.Index("ix_mensaje_interno_destinatario", "tenant_id", "destinatario_id"),
        op.Index("ix_mensaje_interno_hilo", "tenant_id", "hilo_id"),
    )


def downgrade() -> None:
    op.drop_table("mensaje_interno")
