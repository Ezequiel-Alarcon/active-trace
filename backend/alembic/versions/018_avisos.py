"""018: add aviso, acknowledgment_aviso tables and avisos permissions (C-15).

Run order:
    alembic upgrade head
    alembic downgrade -1
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op


revision: str = "018_avisos"
down_revision: Union[str, None] = "017_coloquios_permissions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ── Permission IDs ─────────────────────────────────────────────────────
AVISOS_PUBLICAR_ID = "00000000-0000-0000-0001-c00000000001"
AVISOS_CONFIRMAR_ID = "00000000-0000-0000-0001-c00000000002"

# ── Role IDs ────────────────────────────────────────────────────────────
ALUMNO_ID = "00000000-0000-0000-0000-a00000000002"
TUTOR_ID = "00000000-0000-0000-0000-a00000000003"
COORDINADOR_ID = "00000000-0000-0000-0000-a00000000004"
NEXO_ID = "00000000-0000-0000-0000-a00000000005"
ADMIN_ID = "00000000-0000-0000-0000-a00000000006"
FINANZAS_ID = "00000000-0000-0000-0000-a00000000007"
PROFESOR_ID = "00000000-0000-0000-0000-a00000000008"

GLOBAL_TENANT = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def upgrade() -> None:
    # ── aviso table ──────────────────────────────────────────────────
    op.create_table(
        "aviso",
        op.Column("id", op.UUID(), primary_key=True),
        op.Column("tenant_id", op.UUID(), nullable=False),
        op.Column("created_at", op.DateTime(timezone=True), nullable=False, server_default=op.text("now()")),
        op.Column("updated_at", op.DateTime(timezone=True), nullable=False, server_default=op.text("now()")),
        op.Column("deleted_at", op.DateTime(timezone=True), nullable=True),
        op.Column("titulo", op.String(255), nullable=False),
        op.Column("cuerpo", op.Text(), nullable=False),
        op.Column(
            "alcance",
            op.Enum("Global", "PorMateria", "PorCohorte", "PorRol", name="alcance_aviso"),
            nullable=False,
        ),
        op.Column(
            "severidad",
            op.Enum("Info", "Advertencia", "Crítico", name="severidad_aviso"),
            nullable=False,
            server_default="Info",
        ),
        op.Column("rol_destino", op.String(64), nullable=True),
        op.Column("materia_id", op.UUID(), nullable=True),
        op.Column("cohorte_id", op.UUID(), nullable=True),
        op.Column("inicio_en", op.DateTime(timezone=True), nullable=True),
        op.Column("fin_en", op.DateTime(timezone=True), nullable=True),
        op.Column("orden", op.Integer(), nullable=False, server_default=op.text("0")),
        op.Column("activo", op.Boolean(), nullable=False, server_default=op.text("true")),
        op.Column("requiere_ack", op.Boolean(), nullable=False, server_default=op.text("false")),
        op.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="RESTRICT"),
        op.Index("ix_aviso_tenant", "tenant_id"),
        op.Index("ix_aviso_tenant_deleted", "tenant_id", "deleted_at"),
        op.Index("ix_aviso_tenant_alcance", "tenant_id", "alcance"),
        op.Index("ix_aviso_tenant_activo", "tenant_id", "activo", "inicio_en", "fin_en"),
    )

    # ── acknowledgment_aviso table ───────────────────────────────────
    op.create_table(
        "acknowledgment_aviso",
        op.Column("id", op.UUID(), primary_key=True),
        op.Column("tenant_id", op.UUID(), nullable=False),
        op.Column("created_at", op.DateTime(timezone=True), nullable=False, server_default=op.text("now()")),
        op.Column("updated_at", op.DateTime(timezone=True), nullable=False, server_default=op.text("now()")),
        op.Column("deleted_at", op.DateTime(timezone=True), nullable=True),
        op.Column("aviso_id", op.UUID(), nullable=False),
        op.Column("usuario_id", op.UUID(), nullable=False),
        op.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="RESTRICT"),
        op.ForeignKeyConstraint(["aviso_id"], ["aviso.id"], ondelete="CASCADE"),
        op.Index("ix_ack_aviso_tenant_aviso", "tenant_id", "aviso_id"),
        op.Index("ix_ack_aviso_tenant_usuario", "tenant_id", "usuario_id"),
        op.Index(
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
