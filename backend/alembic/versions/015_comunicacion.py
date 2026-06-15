"""015: add comunicacion table and tenant.umbral_aprobacion (C-12).

Run order:
    alembic upgrade head
    alembic downgrade -1
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ENUM as pg_ENUM


revision: str = "015_comunicacion"
down_revision: Union[str, None] = "014_analisis_actividades"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # TODO: (HACK) pg_ENUM(create_type=False) en SQLAlchemy 2.0 no garantiza
    # idempotencia en re-ejecuciones. El DO $$ block con EXCEPTION WHEN
    # duplicate_object hace el CREATE TYPE idempotente. Ver mismo patrón en
    # 016_evaluaciones.py y 018_avisos.py.
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE comunicacion_estado AS ENUM ('Pendiente', 'Enviando', 'Enviado', 'Error', 'Cancelado');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.add_column(
        "tenant",
        sa.Column("umbral_aprobacion", sa.Integer(), nullable=False, server_default="10"),
    )
    op.execute("COMMENT ON COLUMN tenant.umbral_aprobacion IS 'Threshold for comunicacion approval'")

    op.create_table(
        "comunicacion",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("asunto", sa.String(500), nullable=False),
        sa.Column("cuerpo", sa.Text(), nullable=False),
        sa.Column("destinatario", sa.String(255), nullable=False),
        sa.Column(
            "estado",
            pg_ENUM("Pendiente", "Enviando", "Enviado", "Error", "Cancelado", name="comunicacion_estado", create_type=False),
            nullable=False,
            server_default="Pendiente",
        ),
        sa.Column("lote_id", sa.UUID(), nullable=True),
        sa.Column("error_detail", sa.Text(), nullable=True),
        sa.Column("enviado_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="RESTRICT"),
        sa.Index("ix_comunicacion_estado", "estado"),
        sa.Index("ix_comunicacion_lote_id", "lote_id"),
        sa.Index("ix_comunicacion_tenant_estado", "tenant_id", "estado"),
        sa.Index("ix_comunicacion_tenant_deleted", "tenant_id", "deleted_at"),
    )


def downgrade() -> None:
    op.drop_table("comunicacion")
    op.drop_column("tenant", "umbral_aprobacion")
    op.execute("DROP TYPE IF EXISTS comunicacion_estado")