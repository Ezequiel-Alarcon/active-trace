"""016: add evaluacion, reserva_evaluacion, resultado_evaluacion tables (C-14).

Run order:
    alembic upgrade head
    alembic downgrade -1
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op


revision: str = "016_evaluaciones"
down_revision: Union[str, None] = "015_comunicacion"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "evaluacion",
        op.Column("id", op.UUID(), primary_key=True),
        op.Column("tenant_id", op.UUID(), nullable=False),
        op.Column("created_at", op.DateTime(timezone=True), nullable=False, server_default=op.text("now()")),
        op.Column("updated_at", op.DateTime(timezone=True), nullable=False, server_default=op.text("now()")),
        op.Column("deleted_at", op.DateTime(timezone=True), nullable=True),
        op.Column("materia_id", op.UUID(), nullable=False),
        op.Column("cohorte_id", op.UUID(), nullable=False),
        op.Column(
            "tipo",
            op.Enum("Parcial", "TP", "Coloquio", "Recuperatorio", name="evaluacion_tipo"),
            nullable=False,
            server_default="Coloquio",
        ),
        op.Column("instancia", op.String(255), nullable=False),
        op.Column("dias_disponibles", op.Integer(), nullable=False),
        op.Column("cupos", op.Integer(), nullable=False),
        op.Column("fecha_inicio", op.Date(), nullable=False),
        op.Column("dias", op.JSONB(), nullable=False),
        op.Column(
            "estado",
            op.Enum("Abierta", "Cerrada", name="evaluacion_estado"),
            nullable=False,
            server_default="Abierta",
        ),
        op.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="RESTRICT"),
        op.ForeignKeyConstraint(["materia_id"], ["materia.id"], ondelete="RESTRICT"),
        op.ForeignKeyConstraint(["cohorte_id"], ["cohorte.id"], ondelete="RESTRICT"),
        op.Index("ix_evaluacion_tenant_materia", "tenant_id", "materia_id"),
        op.Index("ix_evaluacion_tenant_cohorte", "tenant_id", "cohorte_id"),
        op.Index("ix_evaluacion_tenant_deleted", "tenant_id", "deleted_at"),
        op.Index("ix_evaluacion_tenant_estado", "tenant_id", "estado"),
    )

    op.create_table(
        "reserva_evaluacion",
        op.Column("id", op.UUID(), primary_key=True),
        op.Column("tenant_id", op.UUID(), nullable=False),
        op.Column("created_at", op.DateTime(timezone=True), nullable=False, server_default=op.text("now()")),
        op.Column("updated_at", op.DateTime(timezone=True), nullable=False, server_default=op.text("now()")),
        op.Column("deleted_at", op.DateTime(timezone=True), nullable=True),
        op.Column("evaluacion_id", op.UUID(), nullable=False),
        op.Column("alumno_id", op.UUID(), nullable=False),
        op.Column("fecha_reserva", op.Date(), nullable=False),
        op.Column(
            "estado",
            op.Enum("Activa", "Cancelada", name="reserva_estado"),
            nullable=False,
            server_default="Activa",
        ),
        op.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="RESTRICT"),
        op.ForeignKeyConstraint(["evaluacion_id"], ["evaluacion.id"], ondelete="CASCADE"),
        op.ForeignKeyConstraint(["alumno_id"], ["usuario.id"], ondelete="RESTRICT"),
        op.Index("ix_reserva_evaluacion_tenant_evaluacion", "tenant_id", "evaluacion_id"),
        op.Index("ix_reserva_evaluacion_tenant_alumno", "tenant_id", "alumno_id"),
        op.Index("ix_reserva_evaluacion_tenant_deleted", "tenant_id", "deleted_at"),
        op.UniqueConstraint("tenant_id", "evaluacion_id", "alumno_id", name="ix_reserva_evaluacion_unique_active"),
    )

    op.create_table(
        "resultado_evaluacion",
        op.Column("id", op.UUID(), primary_key=True),
        op.Column("tenant_id", op.UUID(), nullable=False),
        op.Column("created_at", op.DateTime(timezone=True), nullable=False, server_default=op.text("now()")),
        op.Column("updated_at", op.DateTime(timezone=True), nullable=False, server_default=op.text("now()")),
        op.Column("deleted_at", op.DateTime(timezone=True), nullable=True),
        op.Column("evaluacion_id", op.UUID(), nullable=False),
        op.Column("alumno_id", op.UUID(), nullable=False),
        op.Column("nota_final", op.Text(), nullable=True),
        op.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="RESTRICT"),
        op.ForeignKeyConstraint(["evaluacion_id"], ["evaluacion.id"], ondelete="CASCADE"),
        op.ForeignKeyConstraint(["alumno_id"], ["usuario.id"], ondelete="RESTRICT"),
        op.Index("ix_resultado_evaluacion_tenant_evaluacion", "tenant_id", "evaluacion_id"),
        op.Index("ix_resultado_evaluacion_tenant_alumno", "tenant_id", "alumno_id"),
        op.Index("ix_resultado_evaluacion_tenant_deleted", "tenant_id", "deleted_at"),
        op.UniqueConstraint("tenant_id", "evaluacion_id", "alumno_id", name="ix_resultado_evaluacion_unique"),
    )


def downgrade() -> None:
    op.drop_table("resultado_evaluacion")
    op.drop_table("reserva_evaluacion")
    op.drop_table("evaluacion")
    op.execute("DROP TYPE IF EXISTS evaluacion_estado")
    op.execute("DROP TYPE IF EXISTS reserva_estado")
    op.execute("DROP TYPE IF EXISTS evaluacion_tipo")