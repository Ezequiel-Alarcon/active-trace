"""RBAC domain models (C-04 §2).

Three tables, all inheriting TenantScopedMixin for the standard multi-tenant
contract (id, tenant_id, created_at, updated_at, deleted_at):

- Rol: role catalog entry (ALUMNO, PROFESOR, ADMIN, ...)
- Permiso: atomic permission expressed as modulo:accion
- RolPermiso: many-to-many junction (rol_id, permiso_id) with tenant scope
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import (
    ForeignKey,
    Index,
    String,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import TenantScopedMixin


class Rol(TenantScopedMixin, Base):
    """A role in the RBAC catalog. Named uniquely within a tenant."""

    __tablename__ = "rol"

    nombre: Mapped[str] = mapped_column(String(64), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(255), nullable=True)

    permisos: Mapped[list["Permiso"]] = relationship(
        "Permiso",
        secondary="rol_permiso",
        back_populates="roles",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_rol_tenant_nombre", "tenant_id", "nombre", unique=True),
        Index("ix_rol_tenant_deleted", "tenant_id", "deleted_at"),
    )


class Permiso(TenantScopedMixin, Base):
    """An atomic permission expressed as modulo:accion."""

    __tablename__ = "permiso"

    modulo: Mapped[str] = mapped_column(String(64), nullable=False)
    accion: Mapped[str] = mapped_column(String(64), nullable=False)

    roles: Mapped[list["Rol"]] = relationship(
        "Rol",
        secondary="rol_permiso",
        back_populates="permisos",
        lazy="selectin",
    )

    __table_args__ = (
        Index(
            "ix_permiso_tenant_modulo_accion",
            "tenant_id",
            "modulo",
            "accion",
            unique=True,
        ),
        Index("ix_permiso_tenant_deleted", "tenant_id", "deleted_at"),
    )


class RolPermiso(TenantScopedMixin, Base):
    """Many-to-many junction between Rol and Permiso, tenant-scoped."""

    __tablename__ = "rol_permiso"

    rol_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("rol.id", ondelete="CASCADE"),
        nullable=False,
    )
    permiso_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("permiso.id", ondelete="CASCADE"),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_rol_permiso_tenant_rol", "tenant_id", "rol_id"),
        Index("ix_rol_permiso_tenant_permiso", "tenant_id", "permiso_id"),
        Index(
            "ix_rol_permiso_tenant_rol_permiso",
            "tenant_id",
            "rol_id",
            "permiso_id",
            unique=True,
        ),
    )
