"""006: usuarios_asignaciones — usuario y asignacion (C-07).

Run order:
    alembic upgrade head    # creates tables
    alembic downgrade -1    # drops both (CASCADE)
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "006_usuarios_asignaciones"
down_revision: Union[str, None] = "005_estructura_academica"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE contexto_tipo AS ENUM ('Global', 'Carrera', 'Cohorte', 'Materia')")

    op.create_table(
        "usuario",
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
        sa.Column("email_hash", sa.String(length=64), nullable=False),
        sa.Column("email_enc", sa.String(length=2048), nullable=False),
        sa.Column("dni_enc", sa.String(length=2048), nullable=False),
        sa.Column("cuil_enc", sa.String(length=2048), nullable=False),
        sa.Column("cbu_enc", sa.String(length=2048), nullable=False),
        sa.Column("alias_cbu_enc", sa.String(length=2048), nullable=True),
        sa.Column("nombre", sa.String(length=128), nullable=False),
        sa.Column("apellidos", sa.String(length=255), nullable=False),
        sa.Column("banco", sa.String(length=128), nullable=True),
        sa.Column("regional", sa.String(length=128), nullable=True),
        sa.Column("legajo", sa.String(length=64), nullable=True),
        sa.Column("legajo_profesional", sa.String(length=64), nullable=True),
        sa.Column("fecha_nacimiento", sa.Date(), nullable=True),
        sa.Column("genero", sa.String(length=16), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
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
        "ix_usuario_tenant_email_hash",
        "usuario",
        ["tenant_id", "email_hash"],
        unique=True,
    )
    op.create_index(
        "ix_usuario_tenant_deleted", "usuario", ["tenant_id", "deleted_at"]
    )

    contexto_tipo_enum = postgresql.ENUM(
        "Global", "Carrera", "Cohorte", "Materia",
        name="contexto_tipo",
        create_type=False,
    )

    op.create_table(
        "asignacion",
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
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuario.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "rol_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("rol.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "contexto_tipo",
            contexto_tipo_enum,
            nullable=False,
        ),
        sa.Column(
            "contexto_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "responsable_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuario.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("desde", sa.Date(), nullable=False),
        sa.Column("hasta", sa.Date(), nullable=True),
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
        "ix_asignacion_tenant_usuario",
        "asignacion",
        ["tenant_id", "usuario_id"],
    )
    op.create_index(
        "ix_asignacion_tenant_rol",
        "asignacion",
        ["tenant_id", "rol_id"],
    )
    op.create_index(
        "ix_asignacion_tenant_contexto",
        "asignacion",
        ["tenant_id", "contexto_tipo", "contexto_id"],
    )
    op.create_index(
        "ix_asignacion_tenant_deleted",
        "asignacion",
        ["tenant_id", "deleted_at"],
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS asignacion CASCADE")
    op.execute("DROP TABLE IF EXISTS usuario CASCADE")
    postgresql.ENUM(name="contexto_tipo", create_type=False).drop(
        op.get_bind(), checkfirst=True
    )
