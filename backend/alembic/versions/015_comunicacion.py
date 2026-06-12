"""015: add comunicacion table and tenant.umbral_aprobacion (C-12).

Run order:
    alembic upgrade head
    alembic downgrade -1
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op


revision: str = "015_comunicacion"
down_revision: Union[str, None] = "014_analisis_actividades"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tenant",
        op.Column("umbral_aprobacion", op.Integer(), nullable=False, server_default="10"),
    )
    op.execute("COMMENT ON COLUMN tenant.umbral_aprobacion IS 'Threshold for comunicacion approval'")

    op.create_table(
        "comunicacion",
        op.Column("id", op.UUID(), primary_key=True),
        op.Column("tenant_id", op.UUID(), nullable=False),
        op.Column("created_at", op.DateTime(timezone=True), nullable=False, server_default=op.text("now()")),
        op.Column("updated_at", op.DateTime(timezone=True), nullable=False, server_default=op.text("now()")),
        op.Column("deleted_at", op.DateTime(timezone=True), nullable=True),
        op.Column("asunto", op.String(500), nullable=False),
        op.Column("cuerpo", op.Text(), nullable=False),
        op.Column("destinatario", op.String(255), nullable=False),
        op.Column(
            "estado",
            op.Enum("Pendiente", "Enviando", "Enviado", "Error", "Cancelado", name="comunicacion_estado"),
            nullable=False,
            server_default="Pendiente",
        ),
        op.Column("lote_id", op.UUID(), nullable=True),
        op.Column("error_detail", op.Text(), nullable=True),
        op.Column("enviado_at", op.DateTime(timezone=True), nullable=True),
        op.Column("retry_count", op.Integer(), nullable=False, server_default="0"),
        op.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="RESTRICT"),
        op.Index("ix_comunicacion_estado", "estado"),
        op.Index("ix_comunicacion_lote_id", "lote_id"),
        op.Index("ix_comunicacion_tenant_estado", "tenant_id", "estado"),
        op.Index("ix_comunicacion_tenant_deleted", "tenant_id", "deleted_at"),
    )


def downgrade() -> None:
    op.drop_table("comunicacion")
    op.drop_column("tenant", "umbral_aprobacion")