"""023: liquidaciones y honorarios (C-18)."""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "023_liquidaciones_honorarios"
down_revision: Union[str, None] = "022_padron_vaciar_permission"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

GLOBAL_TENANT = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
FINANZAS_ID = "00000000-0000-0000-0000-a00000000007"

PERMISSIONS = [
    ("00000000-0000-0000-0001-a00000000030", "liquidaciones", "ver"),
    ("00000000-0000-0000-0001-a00000000031", "liquidaciones", "calcular"),
    ("00000000-0000-0000-0001-a00000000032", "liquidaciones", "cerrar"),
    ("00000000-0000-0000-0001-a00000000033", "liquidaciones", "exportar"),
    ("00000000-0000-0000-0001-a00000000034", "liquidaciones", "configurar-salarios"),
    ("00000000-0000-0000-0001-a00000000035", "facturas", "ver"),
    ("00000000-0000-0000-0001-a00000000036", "facturas", "gestionar"),
    ("00000000-0000-0000-0001-a00000000037", "facturas", "descargar"),
]


def upgrade() -> None:
    op.create_table(
        "plus_categoria",
        sa.Column("grupo", sa.String(length=32), primary_key=True),
        sa.Column("descripcion", sa.String(length=255), nullable=False),
    )
    op.execute("""
        INSERT INTO plus_categoria (grupo, descripcion) VALUES
        ('PROG', 'Materias de programacion'),
        ('MAT', 'Materias matematicas'),
        ('IDI', 'Materias de idiomas')
        ON CONFLICT (grupo) DO NOTHING
    """)

    op.add_column("usuario", sa.Column("facturante", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("materia", sa.Column("plus_grupo", sa.String(length=32), nullable=True))
    op.create_foreign_key("fk_materia_plus_grupo", "materia", "plus_categoria", ["plus_grupo"], ["grupo"], ondelete="RESTRICT")
    op.create_index("ix_materia_plus_grupo", "materia", ["plus_grupo"])
    op.add_column("asignacion", sa.Column("materia_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("asignacion", sa.Column("cohorte_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("asignacion", sa.Column("comisiones", postgresql.JSONB(), server_default="[]", nullable=False))
    op.create_index("ix_asignacion_tenant_materia", "asignacion", ["tenant_id", "materia_id"])
    op.create_index("ix_asignacion_tenant_cohorte", "asignacion", ["tenant_id", "cohorte_id"])

    op.create_table(
        "salario_base",
        sa.Column("rol", sa.String(length=64), nullable=False),
        sa.Column("monto", sa.Numeric(12, 2), nullable=False),
        sa.Column("desde", sa.Date(), nullable=False),
        sa.Column("hasta", sa.Date(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenant.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_salario_base_tenant_rol", "salario_base", ["tenant_id", "rol"])
    op.create_index("ix_salario_base_tenant_deleted", "salario_base", ["tenant_id", "deleted_at"])

    op.create_table(
        "salario_plus",
        sa.Column("grupo", sa.String(length=32), sa.ForeignKey("plus_categoria.grupo"), nullable=False),
        sa.Column("rol", sa.String(length=64), nullable=False),
        sa.Column("descripcion", sa.String(length=255), nullable=False),
        sa.Column("monto", sa.Numeric(12, 2), nullable=False),
        sa.Column("desde", sa.Date(), nullable=False),
        sa.Column("hasta", sa.Date(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenant.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_salario_plus_tenant_grupo_rol", "salario_plus", ["tenant_id", "grupo", "rol"])
    op.create_index("ix_salario_plus_tenant_deleted", "salario_plus", ["tenant_id", "deleted_at"])

    op.create_table(
        "liquidacion",
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rol", sa.String(length=64), nullable=False),
        sa.Column("cohorte_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("periodo", sa.String(length=7), nullable=False),
        sa.Column("monto_base", sa.Numeric(12, 2), nullable=False),
        sa.Column("monto_plus", sa.Numeric(12, 2), nullable=False),
        sa.Column("total", sa.Numeric(12, 2), nullable=False),
        sa.Column("comisiones", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("es_nexo", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("excluido_por_factura", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("estado", sa.Enum("Abierta", "Cerrada", name="liquidacion_estado"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenant.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_liquidacion_tenant_periodo", "liquidacion", ["tenant_id", "cohorte_id", "periodo"])
    op.create_index("ix_liquidacion_tenant_usuario", "liquidacion", ["tenant_id", "usuario_id"])
    op.create_index("ix_liquidacion_tenant_deleted", "liquidacion", ["tenant_id", "deleted_at"])

    op.create_table(
        "factura",
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("periodo", sa.String(length=7), nullable=False),
        sa.Column("detalle", sa.String(length=1000), nullable=False),
        sa.Column("referencia_archivo", sa.String(length=512), nullable=False),
        sa.Column("tamano_kb", sa.Integer(), nullable=False),
        sa.Column("estado", sa.Enum("Pendiente", "Abonada", name="factura_estado"), nullable=False),
        sa.Column("cargada_at", sa.Date(), nullable=False),
        sa.Column("abonada_at", sa.Date(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenant.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_factura_tenant_usuario_periodo", "factura", ["tenant_id", "usuario_id", "periodo"])
    op.create_index("ix_factura_tenant_estado", "factura", ["tenant_id", "estado"])
    op.create_index("ix_factura_tenant_deleted", "factura", ["tenant_id", "deleted_at"])

    values = ",".join(
        f"('{pid}', '{GLOBAL_TENANT}', '{mod}', '{acc}', now(), now(), NULL)" for pid, mod, acc in PERMISSIONS
    )
    op.execute(f"""
        INSERT INTO permiso (id, tenant_id, modulo, accion, created_at, updated_at, deleted_at)
        VALUES {values}
        ON CONFLICT (tenant_id, modulo, accion) DO NOTHING
    """)
    rp_values = ",".join(
        f"(gen_random_uuid(), '{GLOBAL_TENANT}', '{FINANZAS_ID}', '{pid}', now())" for pid, _mod, _acc in PERMISSIONS
    )
    op.execute(f"""
        INSERT INTO rol_permiso (id, tenant_id, rol_id, permiso_id, created_at)
        VALUES {rp_values}
        ON CONFLICT (tenant_id, rol_id, permiso_id) DO NOTHING
    """)


def downgrade() -> None:
    for pid, _mod, _acc in PERMISSIONS:
        op.execute(f"DELETE FROM rol_permiso WHERE permiso_id = '{pid}'")
        op.execute(f"DELETE FROM permiso WHERE id = '{pid}'")
    op.drop_table("factura")
    op.drop_table("liquidacion")
    op.drop_table("salario_plus")
    op.drop_table("salario_base")
    op.drop_index("ix_asignacion_tenant_cohorte", table_name="asignacion")
    op.drop_index("ix_asignacion_tenant_materia", table_name="asignacion")
    op.drop_column("asignacion", "comisiones")
    op.drop_column("asignacion", "cohorte_id")
    op.drop_column("asignacion", "materia_id")
    op.drop_index("ix_materia_plus_grupo", table_name="materia")
    op.drop_constraint("fk_materia_plus_grupo", "materia", type_="foreignkey")
    op.drop_column("materia", "plus_grupo")
    op.drop_column("usuario", "facturante")
    op.drop_table("plus_categoria")
    op.execute("DROP TYPE IF EXISTS liquidacion_estado")
    op.execute("DROP TYPE IF EXISTS factura_estado")
