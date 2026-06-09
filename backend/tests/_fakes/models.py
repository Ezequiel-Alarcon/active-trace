"""Test-only models for repository and isolation tests.

The `Smoke` model is a stand-in for a domain entity. It exists ONLY in
the test process; it is never imported by application code and is NOT
included in Alembic migrations.

If you need additional shapes for testing (e.g. a non-tenant-scoped
catalog, a model with a unique constraint), add it here.
"""

from __future__ import annotations

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TenantScopedMixin


class Smoke(TenantScopedMixin, Base):
    """A `TenantScopedMixin` carrier used to exercise the repository base."""

    __tablename__ = "_smoke_tests"

    label: Mapped[str] = mapped_column(String(64), nullable=False)

    __table_args__ = (
        Index("ix_smoke_tenant", "tenant_id"),
        Index("ix_smoke_tenant_deleted", "tenant_id", "deleted_at"),
    )
