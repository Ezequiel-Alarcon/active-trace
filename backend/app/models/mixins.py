"""Reusable mixins for activia-trace domain models.

These are the building blocks that make multi-tenancy + soft delete
enforced by construction (see design.md D2 and D3).

Conventions:
- `TenantScopedMixin` is the canonical base for every domain entity.
  It provides UUID `id`, `tenant_id` FK ON DELETE RESTRICT, created/updated
  timestamps, and the soft delete column. Indexes are declared by each
  concrete model in its own `__table_args__` so the index name matches the
  table name per the project naming convention (`ix_<tabla>_tenant`,
  `ix_<tabla>_tenant_deleted`).
- `SoftDeleteMixin` is a stand-alone version of just the soft-delete column
  for tables that are NOT tenant-scoped (e.g. the `tenant` table itself,
  which is the root of the multi-tenant model and therefore has no
  `tenant_id` of its own).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column


class SoftDeleteMixin:
    """Adds a nullable `deleted_at` timestamp for soft delete.

    Stand-alone use only (e.g. the `tenant` table). Domain entities should
    use `TenantScopedMixin`, which already includes this column.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )


class TenantScopedMixin(SoftDeleteMixin):
    """The standard domain-entity base.

    Adds:
    - `id`: UUID PK, default `uuid4()`.
    - `tenant_id`: UUID, NOT NULL, FK to `tenant.id` ON DELETE RESTRICT.
    - `created_at`: server-side default `now()`.
    - `updated_at`: server-side default `now()` + ON UPDATE `now()`.
    - `deleted_at`: nullable, default null (soft delete).

    Indexes are NOT declared here on purpose: SQLAlchemy needs the table
    name to apply the project's naming convention. Each concrete model
    declares its `__table_args__` with `Index("ix_<tabla>_tenant", ...)`
    and `Index("ix_<tabla>_tenant_deleted", "tenant_id", "deleted_at")`.
    """

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("tenant.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
