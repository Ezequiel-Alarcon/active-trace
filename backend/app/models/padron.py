"""Padron models — versionado de padrón de alumnos (C-09).

VersionPadron: una versión del padrón por (materia_id, cohorte_id).
EntradaPadron: cada alumno en el padrón, vinculado a una versión.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models.base import Base
from app.models.mixins import TenantScopedMixin


class VersionPadron(Base, TenantScopedMixin):
    __tablename__ = "version_padron"

    materia_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    cohorte_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    cargado_por: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    cargado_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    activa: Mapped[bool] = mapped_column(nullable=False, default=False)
    actividades: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    entradas: Mapped[list[EntradaPadron]] = relationship(
        "EntradaPadron",
        back_populates="version",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_version_padron_tenant", "tenant_id"),
        Index("ix_version_padron_materia_cohorte_activa", "materia_id", "cohorte_id", "activa"),
        Index("ix_version_padron_tenant_deleted", "tenant_id", "deleted_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<VersionPadron id={self.id!r} materia_id={self.materia_id!r} "
            f"cohorte_id={self.cohorte_id!r} activa={self.activa!r}>"
        )


class EntradaPadron(Base, TenantScopedMixin):
    __tablename__ = "entrada_padron"

    version_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("version_padron.id", ondelete="CASCADE"),
        nullable=False,
    )
    usuario_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    nombre: Mapped[str] = mapped_column(String(128), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(2048), nullable=False)
    comision: Mapped[str | None] = mapped_column(String(64), nullable=True)
    regional: Mapped[str | None] = mapped_column(String(128), nullable=True)

    version: Mapped[VersionPadron] = relationship("VersionPadron", back_populates="entradas")

    __table_args__ = (
        Index("ix_entrada_padron_tenant", "tenant_id"),
        Index("ix_entrada_padron_version", "version_id"),
        Index("ix_entrada_padron_usuario", "usuario_id"),
        Index("ix_entrada_padron_tenant_deleted", "tenant_id", "deleted_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<EntradaPadron id={self.id!r} nombre={self.nombre!r} "
            f"apellidos={self.apellidos!r} usuario_id={self.usuario_id!r}>"
        )