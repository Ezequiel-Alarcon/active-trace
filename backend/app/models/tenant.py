"""`tenant` table — root of the multi-tenant data model.

This is the ONLY table that does NOT inherit from `TenantScopedMixin`,
because it is the root that other tables FK into. It does still inherit
`SoftDeleteMixin` for the soft-delete contract.
"""

from __future__ import annotations

import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Index, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import SoftDeleteMixin


class TenantEstado(str, enum.Enum):
    """Estado de un tenant en la plataforma."""

    ACTIVO = "Activo"
    INACTIVO = "Inactivo"


class Tenant(Base, SoftDeleteMixin):
    __tablename__ = "tenant"

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    codigo: Mapped[str] = mapped_column(String(64), nullable=False)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    estado: Mapped[TenantEstado] = mapped_column(
        SAEnum(TenantEstado, name="tenant_estado", values_callable=lambda x: [m.value for m in x]),
        nullable=False,
        default=TenantEstado.ACTIVO,
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

    __table_args__ = (
        Index("ux_tenant_codigo", "codigo", unique=True),
        Index("ix_tenant_estado", "estado"),
        Index("ix_tenant_created_at", "created_at"),
        Index("ix_tenant_deleted_at", "deleted_at"),
        CheckConstraint(
            "estado IN ('Activo', 'Inactivo')",
            name="ck_tenant_estado",
        ),
    )
