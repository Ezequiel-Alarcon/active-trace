"""004: rbac_tables — rol, permiso, rol_permiso + seed (C-04 §2, D6).

Run order:
    alembic upgrade head    # creates tables + seed
    alembic downgrade -1    # drops all three (CASCADE)

Naming convention:
    pk_<table>, ix_<table>_<cols>, ux_<table>_<col>
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "004_rbac"
down_revision: Union[str, None] = "003_email_hash"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------- rol ----------
    op.create_table(
        "rol",
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
        sa.Column("nombre", sa.String(length=64), nullable=False),
        sa.Column("descripcion", sa.String(length=255), nullable=True),
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
        "ix_rol_tenant_nombre", "rol", ["tenant_id", "nombre"], unique=True
    )
    op.create_index("ix_rol_tenant_deleted", "rol", ["tenant_id", "deleted_at"])

    # ---------- permiso ----------
    op.create_table(
        "permiso",
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
        sa.Column("modulo", sa.String(length=64), nullable=False),
        sa.Column("accion", sa.String(length=64), nullable=False),
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
        "ix_permiso_tenant_modulo_accion",
        "permiso",
        ["tenant_id", "modulo", "accion"],
        unique=True,
    )
    op.create_index(
        "ix_permiso_tenant_deleted", "permiso", ["tenant_id", "deleted_at"]
    )

    # ---------- rol_permiso ----------
    op.create_table(
        "rol_permiso",
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
            "rol_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("rol.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "permiso_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("permiso.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_rol_permiso_tenant_rol", "rol_permiso", ["tenant_id", "rol_id"]
    )
    op.create_index(
        "ix_rol_permiso_tenant_permiso",
        "rol_permiso",
        ["tenant_id", "permiso_id"],
    )
    op.create_index(
        "ix_rol_permiso_tenant_rol_permiso",
        "rol_permiso",
        ["tenant_id", "rol_id", "permiso_id"],
        unique=True,
    )

    # ---------- seed data ----------
    # GLOBAL_TENANT_ID = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'
    # Seed is universal: roles and permissions are stored under the global tenant.
    # The permission resolver adds global tenant permissions to every real tenant
    # via UNION ALL — so all tenants get the same baseline without per-tenant copies.
    # First, create the global tenant record (needed for FK constraint).
    op.execute("""
        INSERT INTO tenant (id, codigo, nombre, estado, created_at, updated_at, deleted_at)
        VALUES ('aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 'GLOBAL', 'Global System Tenant', 'Activo', now(), now(), NULL)
        ON CONFLICT (id) DO NOTHING
    """)
    # Roles: ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS
    op.execute("""
        INSERT INTO rol (id, tenant_id, nombre, descripcion, created_at, updated_at, deleted_at)
        VALUES
            ('00000000-0000-0000-0000-a00000000001', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 'ALUMNO',      'Estudiante que cursa materias', now(), now(), NULL),
            ('00000000-0000-0000-0000-a00000000002', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 'TUTOR',       'Auxiliar / ayudante de catedra',             now(), now(), NULL),
            ('00000000-0000-0000-0000-a00000000003', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 'PROFESOR',    'Docente a cargo de una o mas comisiones',      now(), now(), NULL),
            ('00000000-0000-0000-0000-a00000000004', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 'COORDINADOR', 'Responsable de un conjunto de materias',     now(), now(), NULL),
            ('00000000-0000-0000-0000-a00000000005', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 'NEXO',        'Rol de articulacion / enlace transversal',     now(), now(), NULL),
            ('00000000-0000-0000-0000-a00000000006', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 'ADMIN',       'Administrador del sistema dentro del tenant',  now(), now(), NULL),
            ('00000000-0000-0000-0000-a00000000007', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 'FINANZAS',    'Responsable de liquidaciones y honorarios',   now(), now(), NULL)
        ON CONFLICT (tenant_id, nombre) DO NOTHING
    """)

    # Permissions: 23 atomic permissions from KB §3.3
    op.execute("""
        INSERT INTO permiso (id, tenant_id, modulo, accion, created_at, updated_at, deleted_at)
        VALUES
            ('00000000-0000-0000-0001-a00000000001', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 'academico',     'ver_estado_propio',   now(), now(), NULL),
            ('00000000-0000-0000-0001-a00000000002', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 'evaluaciones', 'reservar',            now(), now(), NULL),
            ('00000000-0000-0000-0001-a00000000003', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 'avisos',       'confirmar',           now(), now(), NULL),
            ('00000000-0000-0000-0001-a00000000004', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 'calificaciones','importar',           now(), now(), NULL),
            ('00000000-0000-0000-0001-a00000000005', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 'calificaciones','ver',                now(), now(), NULL),
            ('00000000-0000-0000-0001-a00000000006', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 'atrasados',    'ver',                now(), now(), NULL),
            ('00000000-0000-0000-0001-a00000000007', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 'entregas',     'ver_sin_corregir',    now(), now(), NULL),
            ('00000000-0000-0000-0001-a00000000008', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 'comunicacion', 'enviar',              now(), now(), NULL),
            ('00000000-0000-0000-0001-a00000000009', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 'comunicacion', 'aprobar',             now(), now(), NULL),
            ('00000000-0000-0000-0001-a00000000010', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 'encuentros',   'gestionar',           now(), now(), NULL),
            ('00000000-0000-0000-0001-a00000000011', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 'encuentros',   'registrar_guardia',    now(), now(), NULL),
            ('00000000-0000-0000-0001-a00000000012', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 'tareas',       'gestionar',           now(), now(), NULL),
            ('00000000-0000-0000-0001-a00000000013', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 'avisos',      'publicar',            now(), now(), NULL),
            ('00000000-0000-0000-0001-a00000000014', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 'equipos',     'asignar',             now(), now(), NULL),
            ('00000000-0000-0000-0001-a00000000015', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 'estructura',   'gestionar',           now(), now(), NULL),
            ('00000000-0000-0000-0001-a00000000016', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 'usuarios',    'gestionar',           now(), now(), NULL),
            ('00000000-0000-0000-0001-a00000000017', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 'auditoria',   'ver',                 now(), now(), NULL),
            ('00000000-0000-0000-0001-a00000000018', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 'impersonacion','usar',                now(), now(), NULL),
            ('00000000-0000-0000-0001-a00000000019', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 'finanzas',    'operar_grilla',        now(), now(), NULL),
            ('00000000-0000-0000-0001-a00000000020', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 'finanzas',    'cerrar_liquidacion',  now(), now(), NULL),
            ('00000000-0000-0000-0001-a00000000021', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 'finanzas',    'gestionar_facturas',  now(), now(), NULL),
            ('00000000-0000-0000-0001-a00000000022', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 'tenant',      'configurar',           now(), now(), NULL),
            ('00000000-0000-0000-0001-a00000000023', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 'roles',       'gestionar',           now(), now(), NULL)
        ON CONFLICT (tenant_id, modulo, accion) DO NOTHING
    """)

    # RolPermiso matrix — maps each global role to its permissions
    op.execute("""
        INSERT INTO rol_permiso (id, tenant_id, rol_id, permiso_id, created_at)
        VALUES
            -- ALUMNO: academico:ver_estado_propio, evaluaciones:reservar, avisos:confirmar
            ('00000000-0000-0000-0002-a00000000001', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000001', '00000000-0000-0000-0001-a00000000001', now()),
            ('00000000-0000-0000-0002-a00000000002', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000001', '00000000-0000-0000-0001-a00000000002', now()),
            ('00000000-0000-0000-0002-a00000000003', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000001', '00000000-0000-0000-0001-a00000000003', now()),
            -- TUTOR: avisos:confirmar, atrasados:ver, entregas:ver_sin_corregir, encuentros:gestionar, registrar_guardia
            ('00000000-0000-0000-0002-a00000000004', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000002', '00000000-0000-0000-0001-a00000000003', now()),
            ('00000000-0000-0000-0002-a00000000005', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000002', '00000000-0000-0000-0001-a00000000006', now()),
            ('00000000-0000-0000-0002-a00000000006', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000002', '00000000-0000-0000-0001-a00000000007', now()),
            ('00000000-0000-0000-0002-a00000000007', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000002', '00000000-0000-0000-0001-a00000000010', now()),
            ('00000000-0000-0000-0002-a00000000008', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000002', '00000000-0000-0000-0001-a00000000011', now()),
            -- PROFESOR: calificaciones:importar+ver, atrasados:ver, entregas:ver_sin_corregir,
            --           comunicacion:enviar, encuentros:gestionar+registrar_guardia, tareas:gestionar
            ('00000000-0000-0000-0002-a00000000009', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000003', '00000000-0000-0000-0001-a00000000004', now()),
            ('00000000-0000-0000-0002-a00000000010', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000003', '00000000-0000-0000-0001-a00000000005', now()),
            ('00000000-0000-0000-0002-a00000000011', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000003', '00000000-0000-0000-0001-a00000000006', now()),
            ('00000000-0000-0000-0002-a00000000012', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000003', '00000000-0000-0000-0001-a00000000007', now()),
            ('00000000-0000-0000-0002-a00000000013', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000003', '00000000-0000-0000-0001-a00000000008', now()),
            ('00000000-0000-0000-0002-a00000000014', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000003', '00000000-0000-0000-0001-a00000000010', now()),
            ('00000000-0000-0000-0002-a00000000015', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000003', '00000000-0000-0000-0001-a00000000011', now()),
            ('00000000-0000-0000-0002-a00000000016', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000003', '00000000-0000-0000-0001-a00000000012', now()),
            -- COORDINADOR: calificaciones:importar, atrasados:ver, entregas:ver_sin_corregir,
            --             comunicacion:enviar+aprobar, encuentros:gestionar+registrar_guardia,
            --             tareas:gestionar, avisos:publicar, equipos:asignar
            ('00000000-0000-0000-0002-a00000000017', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000004', '00000000-0000-0000-0001-a00000000004', now()),
            ('00000000-0000-0000-0002-a00000000018', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000004', '00000000-0000-0000-0001-a00000000006', now()),
            ('00000000-0000-0000-0002-a00000000019', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000004', '00000000-0000-0000-0001-a00000000007', now()),
            ('00000000-0000-0000-0002-a00000000020', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000004', '00000000-0000-0000-0001-a00000000008', now()),
            ('00000000-0000-0000-0002-a00000000021', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000004', '00000000-0000-0000-0001-a00000000009', now()),
            ('00000000-0000-0000-0002-a00000000022', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000004', '00000000-0000-0000-0001-a00000000010', now()),
            ('00000000-0000-0000-0002-a00000000023', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000004', '00000000-0000-0000-0001-a00000000011', now()),
            ('00000000-0000-0000-0002-a00000000024', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000004', '00000000-0000-0000-0001-a00000000012', now()),
            ('00000000-0000-0000-0002-a00000000025', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000004', '00000000-0000-0000-0001-a00000000013', now()),
            ('00000000-0000-0000-0002-a00000000026', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000004', '00000000-0000-0000-0001-a00000000014', now()),
            -- NEXO: transversal — avisos:confirmar, comunicacion:enviar+aprobar, encuentros:gestionar, auditoria:ver
            ('00000000-0000-0000-0002-a00000000027', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000005', '00000000-0000-0000-0001-a00000000003', now()),
            ('00000000-0000-0000-0002-a00000000028', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000005', '00000000-0000-0000-0001-a00000000008', now()),
            ('00000000-0000-0000-0002-a00000000029', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000005', '00000000-0000-0000-0001-a00000000009', now()),
            ('00000000-0000-0000-0002-a00000000030', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000005', '00000000-0000-0000-0001-a00000000010', now()),
            ('00000000-0000-0000-0002-a00000000031', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000005', '00000000-0000-0000-0001-a00000000017', now()),
            -- ADMIN: all except finanzas:operar_grilla/cerrar_liquidacion/gestionar_facturas
            ('00000000-0000-0000-0002-a00000000032', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000006', '00000000-0000-0000-0001-a00000000003', now()),
            ('00000000-0000-0000-0002-a00000000033', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000006', '00000000-0000-0000-0001-a00000000004', now()),
            ('00000000-0000-0000-0002-a00000000034', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000006', '00000000-0000-0000-0001-a00000000005', now()),
            ('00000000-0000-0000-0002-a00000000035', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000006', '00000000-0000-0000-0001-a00000000006', now()),
            ('00000000-0000-0000-0002-a00000000036', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000006', '00000000-0000-0000-0001-a00000000007', now()),
            ('00000000-0000-0000-0002-a00000000037', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000006', '00000000-0000-0000-0001-a00000000008', now()),
            ('00000000-0000-0000-0002-a00000000038', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000006', '00000000-0000-0000-0001-a00000000009', now()),
            ('00000000-0000-0000-0002-a00000000039', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000006', '00000000-0000-0000-0001-a00000000010', now()),
            ('00000000-0000-0000-0002-a00000000040', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000006', '00000000-0000-0000-0001-a00000000011', now()),
            ('00000000-0000-0000-0002-a00000000041', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000006', '00000000-0000-0000-0001-a00000000012', now()),
            ('00000000-0000-0000-0002-a00000000042', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000006', '00000000-0000-0000-0001-a00000000013', now()),
            ('00000000-0000-0000-0002-a00000000043', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000006', '00000000-0000-0000-0001-a00000000014', now()),
            ('00000000-0000-0000-0002-a00000000044', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000006', '00000000-0000-0000-0001-a00000000015', now()),
            ('00000000-0000-0000-0002-a00000000045', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000006', '00000000-0000-0000-0001-a00000000016', now()),
            ('00000000-0000-0000-0002-a00000000046', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000006', '00000000-0000-0000-0001-a00000000017', now()),
            ('00000000-0000-0000-0002-a00000000047', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000006', '00000000-0000-0000-0001-a00000000022', now()),
            ('00000000-0000-0000-0002-a00000000048', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000006', '00000000-0000-0000-0001-a00000000023', now()),
            -- FINANZAS: finanzas:operar_grilla/cerrar_liquidacion/gestionar_facturas, auditoria:ver
            ('00000000-0000-0000-0002-a00000000049', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000007', '00000000-0000-0000-0001-a00000000019', now()),
            ('00000000-0000-0000-0002-a00000000050', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000007', '00000000-0000-0000-0001-a00000000020', now()),
            ('00000000-0000-0000-0002-a00000000051', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000007', '00000000-0000-0000-0001-a00000000021', now()),
            ('00000000-0000-0000-0002-a00000000052', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '00000000-0000-0000-0000-a00000000007', '00000000-0000-0000-0001-a00000000017', now())
        ON CONFLICT (tenant_id, rol_id, permiso_id) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS rol_permiso CASCADE")
    op.execute("DROP TABLE IF EXISTS permiso CASCADE")
    op.execute("DROP TABLE IF EXISTS rol CASCADE")
    op.execute("DELETE FROM tenant WHERE id = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'")
