"""Auth subsystem ORM models (C-03 §2, D0, D2, D3).

Three tables, all inheriting `TenantScopedMixin` for the standard multi-tenant
contract (id, tenant_id, created_at, updated_at, deleted_at).

Naming convention: `auth_*` is intentional — it signals "credential slice
owned by the auth subsystem" and gives C-07 a clean rename story.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TenantScopedMixin


class AuthUser(TenantScopedMixin, Base):
    """Minimal auth-credential user. C-07 extends with PII completa."""

    __tablename__ = "auth_user"

    email_enc: Mapped[str] = mapped_column(String(2048), nullable=False)
    email_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(1024), nullable=False)
    totp_secret_enc: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    totp_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    failed_login_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("ix_auth_user_tenant_email_hash", "tenant_id", "email_hash"),
        Index("ix_auth_user_tenant_deleted", "tenant_id", "deleted_at"),
    )


class AuthSession(TenantScopedMixin, Base):
    """Refresh-token session row. DB-backed (D2)."""

    __tablename__ = "auth_session"

    user_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("auth_user.id", ondelete="CASCADE"),
        nullable=False,
    )
    refresh_token_hash: Mapped[str] = mapped_column(String(1024), nullable=False)
    jti: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), nullable=False, unique=True, default=uuid4
    )
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ip_origen: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    rotated_to_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("auth_session.id", ondelete="SET NULL"),
        nullable=True,
    )
    replaced_by_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("auth_session.id", ondelete="SET NULL"),
        nullable=True,
    )

    __table_args__ = (
        Index("ix_auth_session_user_revoked", "user_id", "revoked_at"),
        Index("ix_auth_session_tenant_deleted", "tenant_id", "deleted_at"),
    )


class AuthPasswordReset(TenantScopedMixin, Base):
    """Password recovery token row. Token stored as Argon2id hash (D3)."""

    __tablename__ = "auth_password_reset"

    user_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("auth_user.id", ondelete="CASCADE"),
        nullable=False,
    )
    selector: Mapped[str] = mapped_column(String(8), nullable=False, unique=True)
    token_hash: Mapped[str] = mapped_column(String(1024), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index(
            "ux_auth_password_reset_selector",
            "selector",
            unique=True,
        ),
        Index("ix_auth_password_reset_user", "user_id"),
        Index("ix_auth_password_reset_tenant_deleted", "tenant_id", "deleted_at"),
    )
