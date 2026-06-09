"""002: auth_user, auth_session, auth_password_reset (C-03 §2, D0/D2/D3).

Run order:
    alembic upgrade head    # adds three auth tables
    alembic downgrade -1    # drops them (reversible)

Naming convention (see alembic/script.py.mako):
    pk_<table>, fk_<table>_<target>, ux_<table>_<col>, ix_<table>_<cols>.
All three tables inherit TenantScopedMixin: id (UUID PK),
tenant_id (FK tenant.id ON DELETE RESTRICT), created_at, updated_at,
deleted_at.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "002_auth"
down_revision: Union[str, None] = "001_tenant"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------- auth_user ----------
    op.create_table(
        "auth_user",
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
        sa.Column("email_enc", sa.String(length=2048), nullable=False),
        sa.Column("password_hash", sa.String(length=1024), nullable=False),
        sa.Column("totp_secret_enc", sa.String(length=2048), nullable=True),
        sa.Column(
            "totp_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "failed_login_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
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
        "ix_auth_user_tenant_email", "auth_user", ["tenant_id", "email_enc"]
    )
    op.create_index(
        "ix_auth_user_tenant_deleted", "auth_user", ["tenant_id", "deleted_at"]
    )

    # ---------- auth_session ----------
    op.create_table(
        "auth_session",
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
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth_user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("refresh_token_hash", sa.String(length=1024), nullable=False),
        sa.Column("jti", postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_origen", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column(
            "rotated_to_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth_session.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "replaced_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth_session.id", ondelete="SET NULL"),
            nullable=True,
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
    op.create_index(
        "ix_auth_session_user_revoked", "auth_session", ["user_id", "revoked_at"]
    )
    op.create_index(
        "ix_auth_session_tenant_deleted",
        "auth_session",
        ["tenant_id", "deleted_at"],
    )

    # ---------- auth_password_reset ----------
    op.create_table(
        "auth_password_reset",
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
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth_user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("selector", sa.String(length=8), nullable=False),
        sa.Column("token_hash", sa.String(length=1024), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
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
        "ux_auth_password_reset_selector",
        "auth_password_reset",
        ["selector"],
        unique=True,
    )
    op.create_index(
        "ix_auth_password_reset_user", "auth_password_reset", ["user_id"]
    )
    op.create_index(
        "ix_auth_password_reset_tenant_deleted",
        "auth_password_reset",
        ["tenant_id", "deleted_at"],
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS auth_password_reset CASCADE")
    op.execute("DROP TABLE IF EXISTS auth_session CASCADE")
    op.execute("DROP TABLE IF EXISTS auth_user CASCADE")
