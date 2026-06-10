"""`programa_materia` table — documento academico por materia × carrera × cohorte (C-17).

Cada programa pertenece a un tenant y asocia una materia con una carrera
y una cohorte. La unicidad es compuesta por (tenant_id, materia_id, carrera_id,
cohorte_id). El campo referencia_archivo es una string opaca (ruta/URL).
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TenantScopedMixin


class ProgramaMateria(Base, TenantScopedMixin):
    __tablename__ = "programa_materia"

    materia_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("materia.id", ondelete="RESTRICT"),
        nullable=False,
    )
    carrera_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("carrera.id", ondelete="RESTRICT"),
        nullable=False,
    )
    cohorte_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("cohorte.id", ondelete="RESTRICT"),
        nullable=False,
    )
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    referencia_archivo: Mapped[str | None] = mapped_column(
        String(512), nullable=True, default=None
    )

    __table_args__ = (
        Index(
            "ix_programa_materia_tenant_materia_carrera_cohorte",
            "tenant_id",
            "materia_id",
            "carrera_id",
            "cohorte_id",
            unique=True,
        ),
        Index("ix_programa_materia_tenant_deleted", "tenant_id", "deleted_at"),
    )
