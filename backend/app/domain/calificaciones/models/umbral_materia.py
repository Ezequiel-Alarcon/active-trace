"""UmbralMateria model (C-10).

Define el umbral de aprobacion para una materia/asignacion.
Si asignacion_id es null, es el umbral por defecto para la materia.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import Index, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TenantScopedMixin


class UmbralMateria(Base, TenantScopedMixin):
    __tablename__ = "umbral_materia"

    materia_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    asignacion_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    umbral_pct: Mapped[int] = mapped_column(Integer(), nullable=False, default=60)
    conjunto_aprobado: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_umbral_materia_tenant", "tenant_id"),
        Index("ix_umbral_materia_materia", "materia_id"),
        Index("ix_umbral_materia_asignacion", "asignacion_id"),
        Index("ix_umbral_materia_tenant_deleted", "tenant_id", "deleted_at"),
        Index(
            "ix_umbral_materia_materia_asignacion_deleted",
            "materia_id",
            "asignacion_id",
            "deleted_at",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<UmbralMateria id={self.id!r} materia_id={self.materia_id!r} "
            f"asignacion_id={self.asignacion_id!r} umbral_pct={self.umbral_pct!r}>"
        )