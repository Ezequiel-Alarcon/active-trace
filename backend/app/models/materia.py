"""`materia` table — catálogo canónico de materias por tenant (C-06, ADR-006).

Materia es la entidad del catálogo académico. La instancia de dictado
(Materia × Carrera × Cohorte) se implementa en un change futuro
(C-07+). La unicidad es compuesta por (tenant_id, codigo).
"""

from __future__ import annotations

import enum

from sqlalchemy import Enum, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TenantScopedMixin


class MateriaEstado(str, enum.Enum):
    ACTIVA = "Activa"
    INACTIVA = "Inactiva"


class Materia(Base, TenantScopedMixin):
    __tablename__ = "materia"

    codigo: Mapped[str] = mapped_column(String(64), nullable=False)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    estado: Mapped[MateriaEstado] = mapped_column(
        Enum(MateriaEstado, name="materia_estado", values_callable=lambda x: [m.value for m in x]),
        nullable=False,
        default=MateriaEstado.ACTIVA,
    )

    __table_args__ = (
        Index("ix_materia_tenant_codigo", "tenant_id", "codigo", unique=True),
        Index("ix_materia_tenant_deleted", "tenant_id", "deleted_at"),
    )
