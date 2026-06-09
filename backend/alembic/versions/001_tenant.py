"""001: create the `tenant` table (root of the multi-tenant model).

C-02 first migration. Run order:
    alembic upgrade head    # creates the `tenant` table
    alembic downgrade -1    # drops it (reversible)

Naming convention (see alembic/script.py.mako):
    pk_tenant, ux_tenant_codigo, ck_tenant_estado, ix_tenant_*
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "001_tenant"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tenant",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("codigo", sa.String(length=64), nullable=False),
        sa.Column("nombre", sa.String(length=255), nullable=False),
        sa.Column(
            "estado",
            sa.Enum("Activo", "Inactivo", name="tenant_estado"),
            nullable=False,
            server_default="Activo",
        ),
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
    # Naming convention: ux_<table>_<col> for unique indexes.
    op.create_index("ux_tenant_codigo", "tenant", ["codigo"], unique=True)
    op.create_index("ix_tenant_estado", "tenant", ["estado"], unique=False)
    op.create_index("ix_tenant_created_at", "tenant", ["created_at"], unique=False)
    op.create_index("ix_tenant_deleted_at", "tenant", ["deleted_at"], unique=False)
    op.create_check_constraint(
        "ck_tenant_estado",
        "tenant",
        "estado IN ('Activo', 'Inactivo')",
    )


def downgrade() -> None:
    # CASCADE because the `tenant` table is the parent of every
    # `TenantScopedMixin` child. A downgrade from a fresh DB only
    # has no children, but CASCADE is the only safe way to undo
    # a forward migration that may have added other tables since.
    op.execute("DROP TABLE IF EXISTS tenant CASCADE")
    # The indexes are dropped automatically with the table; explicit
    # drops would fail on Postgres 14+ if the table is gone, so we
    # omit them and rely on CASCADE.
    # The ENUM type is dropped automatically with the table on Postgres 13+;
    # for safety, leave an explicit drop.
    sa.Enum(name="tenant_estado").drop(op.get_bind(), checkfirst=True)
