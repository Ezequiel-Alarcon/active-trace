"""016: add evaluacion, reserva_evaluacion, resultado_evaluacion tables (C-14).

Run order:
    alembic upgrade head
    alembic downgrade -1
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB as pg_JSONB
from sqlalchemy.dialects.postgresql import ENUM as pg_ENUM
from alembic import op


revision: str = "016_evaluaciones"
down_revision: Union[str, None] = "015_comunicacion"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # TODO: (HACK) pg_ENUM(create_type=False) en SQLAlchemy 2.0 suprime la
    # emisión del CREATE TYPE al crear la tabla, pero no maneja correctamente
    # el caso en que el tipo ya existe en una segunda ejecución (p.ej. si la
    # migración se re-corre tras un fallo parcial). El DO $$ block con
    # EXCEPTION WHEN duplicate_object es el workaround canónico para garantizar
    # idempotencia sin depender del estado previo del schema.
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE evaluacion_tipo AS ENUM ('Parcial', 'TP', 'Coloquio', 'Recuperatorio');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE evaluacion_estado AS ENUM ('Abierta', 'Cerrada');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE reserva_estado AS ENUM ('Activa', 'Cancelada');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.create_table(
        "evaluacion",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("materia_id", sa.UUID(), nullable=False),
        sa.Column("cohorte_id", sa.UUID(), nullable=False),
        sa.Column(
            "tipo",
            pg_ENUM("Parcial", "TP", "Coloquio", "Recuperatorio", name="evaluacion_tipo", create_type=False),
            nullable=False,
            server_default="Coloquio",
        ),
        sa.Column("instancia", sa.String(255), nullable=False),
        sa.Column("dias_disponibles", sa.Integer(), nullable=False),
        sa.Column("cupos", sa.Integer(), nullable=False),
        sa.Column("fecha_inicio", sa.Date(), nullable=False),
        sa.Column("dias", pg_JSONB(), nullable=False),
        sa.Column(
            "estado",
            pg_ENUM("Abierta", "Cerrada", name="evaluacion_estado", create_type=False),
            nullable=False,
            server_default="Abierta",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohorte.id"], ondelete="RESTRICT"),
        sa.Index("ix_evaluacion_tenant_materia", "tenant_id", "materia_id"),
        sa.Index("ix_evaluacion_tenant_cohorte", "tenant_id", "cohorte_id"),
        sa.Index("ix_evaluacion_tenant_deleted", "tenant_id", "deleted_at"),
        sa.Index("ix_evaluacion_tenant_estado", "tenant_id", "estado"),
    )

    op.create_table(
        "reserva_evaluacion",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evaluacion_id", sa.UUID(), nullable=False),
        sa.Column("alumno_id", sa.UUID(), nullable=False),
        sa.Column("fecha_reserva", sa.Date(), nullable=False),
        sa.Column(
            "estado",
            pg_ENUM("Activa", "Cancelada", name="reserva_estado", create_type=False),
            nullable=False,
            server_default="Activa",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["evaluacion_id"], ["evaluacion.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["alumno_id"], ["usuario.id"], ondelete="RESTRICT"),
        sa.Index("ix_reserva_evaluacion_tenant_evaluacion", "tenant_id", "evaluacion_id"),
        sa.Index("ix_reserva_evaluacion_tenant_alumno", "tenant_id", "alumno_id"),
        sa.Index("ix_reserva_evaluacion_tenant_deleted", "tenant_id", "deleted_at"),
        sa.UniqueConstraint("tenant_id", "evaluacion_id", "alumno_id", name="ix_reserva_evaluacion_unique_active"),
    )

    op.create_table(
        "resultado_evaluacion",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evaluacion_id", sa.UUID(), nullable=False),
        sa.Column("alumno_id", sa.UUID(), nullable=False),
        sa.Column("nota_final", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["evaluacion_id"], ["evaluacion.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["alumno_id"], ["usuario.id"], ondelete="RESTRICT"),
        sa.Index("ix_resultado_evaluacion_tenant_evaluacion", "tenant_id", "evaluacion_id"),
        sa.Index("ix_resultado_evaluacion_tenant_alumno", "tenant_id", "alumno_id"),
        sa.Index("ix_resultado_evaluacion_tenant_deleted", "tenant_id", "deleted_at"),
        sa.UniqueConstraint("tenant_id", "evaluacion_id", "alumno_id", name="ix_resultado_evaluacion_unique"),
    )


def downgrade() -> None:
    op.drop_table("resultado_evaluacion")
    op.drop_table("reserva_evaluacion")
    op.drop_table("evaluacion")
    op.execute("DROP TYPE IF EXISTS evaluacion_estado")
    op.execute("DROP TYPE IF EXISTS reserva_estado")
    op.execute("DROP TYPE IF EXISTS evaluacion_tipo")