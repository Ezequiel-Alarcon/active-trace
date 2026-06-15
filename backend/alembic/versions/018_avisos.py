"""018: add aviso, acknowledgment_aviso tables and avisos permissions (C-15).

Run order:
    alembic upgrade head
    alembic downgrade -1
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as pg_ENUM
from alembic import op


revision: str = "018_avisos"
down_revision: Union[str, None] = "017_coloquios_permissions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ── Permission IDs (from 004_rbac seed) ────────────────────────────────
AVISOS_PUBLICAR_ID = "00000000-0000-0000-0001-a00000000013"
AVISOS_CONFIRMAR_ID = "00000000-0000-0000-0001-a00000000003"

# ── Role IDs (from 004_rbac seed) ───────────────────────────────────────
ALUMNO_ID = "00000000-0000-0000-0000-a00000000001"
TUTOR_ID = "00000000-0000-0000-0000-a00000000002"
PROFESOR_ID = "00000000-0000-0000-0000-a00000000003"
COORDINADOR_ID = "00000000-0000-0000-0000-a00000000004"
NEXO_ID = "00000000-0000-0000-0000-a00000000005"
ADMIN_ID = "00000000-0000-0000-0000-a00000000006"
FINANZAS_ID = "00000000-0000-0000-0000-a00000000007"

GLOBAL_TENANT = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def upgrade() -> None:
    # TODO: (HACK) pg_ENUM(create_type=False) en SQLAlchemy 2.0 no garantiza
    # idempotencia cuando el tipo ya existe. El DO $$ block con EXCEPTION WHEN
    # duplicate_object hace el CREATE TYPE idempotente. Ver mismo patrón en
    # 016_evaluaciones.py y 015_comunicacion.py.
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE alcance_aviso AS ENUM ('Global', 'PorMateria', 'PorCohorte', 'PorRol');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE severidad_aviso AS ENUM ('Info', 'Advertencia', 'Crítico');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # ── aviso table ──────────────────────────────────────────────────
    op.create_table(
        "aviso",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("titulo", sa.String(255), nullable=False),
        sa.Column("cuerpo", sa.Text(), nullable=False),
        sa.Column(
            "alcance",
            pg_ENUM("Global", "PorMateria", "PorCohorte", "PorRol", name="alcance_aviso", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "severidad",
            pg_ENUM("Info", "Advertencia", "Crítico", name="severidad_aviso", create_type=False),
            nullable=False,
            server_default="Info",
        ),
        sa.Column("rol_destino", sa.String(64), nullable=True),
        sa.Column("materia_id", sa.UUID(), nullable=True),
        sa.Column("cohorte_id", sa.UUID(), nullable=True),
        sa.Column("inicio_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fin_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("orden", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("requiere_ack", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="RESTRICT"),
        sa.Index("ix_aviso_tenant", "tenant_id"),
        sa.Index("ix_aviso_tenant_deleted", "tenant_id", "deleted_at"),
        sa.Index("ix_aviso_tenant_alcance", "tenant_id", "alcance"),
        sa.Index("ix_aviso_tenant_activo", "tenant_id", "activo", "inicio_en", "fin_en"),
    )

    # ── acknowledgment_aviso table ───────────────────────────────────
    op.create_table(
        "acknowledgment_aviso",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("aviso_id", sa.UUID(), nullable=False),
        sa.Column("usuario_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["aviso_id"], ["aviso.id"], ondelete="CASCADE"),
        sa.Index("ix_ack_aviso_tenant_aviso", "tenant_id", "aviso_id"),
        sa.Index("ix_ack_aviso_tenant_usuario", "tenant_id", "usuario_id"),
        sa.Index(
            "ix_ack_aviso_tenant_aviso_usuario",
            "tenant_id",
            "aviso_id",
            "usuario_id",
            unique=True,
        ),
    )

    # ── Permission seeds ─────────────────────────────────────────────
    op.execute(f"""
        INSERT INTO permiso (id, tenant_id, modulo, accion, created_at, updated_at, deleted_at)
        VALUES
            ('{AVISOS_PUBLICAR_ID}', '{GLOBAL_TENANT}', 'avisos', 'publicar', now(), now(), NULL),
            ('{AVISOS_CONFIRMAR_ID}', '{GLOBAL_TENANT}', 'avisos', 'confirmar', now(), now(), NULL)
        ON CONFLICT (tenant_id, modulo, accion) DO NOTHING
    """)

    # avisos:publicar → COORDINADOR, ADMIN
    op.execute(f"""
        INSERT INTO rol_permiso (id, tenant_id, rol_id, permiso_id, created_at)
        VALUES
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{COORDINADOR_ID}', '{AVISOS_PUBLICAR_ID}', now()),
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{ADMIN_ID}', '{AVISOS_PUBLICAR_ID}', now())
        ON CONFLICT (tenant_id, rol_id, permiso_id) DO NOTHING
    """)

    # avisos:confirmar → all roles
    op.execute(f"""
        INSERT INTO rol_permiso (id, tenant_id, rol_id, permiso_id, created_at)
        VALUES
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{ALUMNO_ID}', '{AVISOS_CONFIRMAR_ID}', now()),
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{TUTOR_ID}', '{AVISOS_CONFIRMAR_ID}', now()),
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{COORDINADOR_ID}', '{AVISOS_CONFIRMAR_ID}', now()),
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{NEXO_ID}', '{AVISOS_CONFIRMAR_ID}', now()),
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{ADMIN_ID}', '{AVISOS_CONFIRMAR_ID}', now()),
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{FINANZAS_ID}', '{AVISOS_CONFIRMAR_ID}', now()),
            (gen_random_uuid(), '{GLOBAL_TENANT}', '{PROFESOR_ID}', '{AVISOS_CONFIRMAR_ID}', now())
        ON CONFLICT (tenant_id, rol_id, permiso_id) DO NOTHING
    """)


def downgrade() -> None:
    op.execute(
        f"DELETE FROM rol_permiso WHERE permiso_id IN ('{AVISOS_PUBLICAR_ID}', '{AVISOS_CONFIRMAR_ID}')"
    )
    op.execute(
        f"DELETE FROM permiso WHERE id IN ('{AVISOS_PUBLICAR_ID}', '{AVISOS_CONFIRMAR_ID}')"
    )
    op.drop_table("acknowledgment_aviso")
    op.drop_table("aviso")
    op.execute("DROP TYPE IF EXISTS alcance_aviso")
    op.execute("DROP TYPE IF EXISTS severidad_aviso")
