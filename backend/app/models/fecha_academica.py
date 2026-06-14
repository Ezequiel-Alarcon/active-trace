"""`fecha_academica` table — fechas de parciales, TP y coloquios (C-17).

Cada fecha representa un evento evaluativo para una materia en una cohorte,
con un tipo y numero de instancia. La unicidad es compuesta por
(tenant_id, materia_id, cohorte_id, tipo, numero_instancia).
"""

from __future__ import annotations

import enum
from datetime import date
from uuid import UUID

from sqlalchemy import Date, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TenantScopedMixin


class TipoFechaAcademica(str, enum.Enum):
    PARCIAL = "Parcial"
    TP = "TP"
    COLOQUIO = "Coloquio"


class FechaAcademica(Base, TenantScopedMixin):
    __tablename__ = "fecha_academica"

    materia_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("materia.id", ondelete="RESTRICT"),
        nullable=False,
    )
    cohorte_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("cohorte.id", ondelete="RESTRICT"),
        nullable=False,
    )
    tipo: Mapped[TipoFechaAcademica] = mapped_column(
        Enum(
            TipoFechaAcademica,
            name="tipo_fecha_academica",
            values_callable=lambda x: [m.value for m in x],
        ),
        nullable=False,
    )
    numero_instancia: Mapped[int] = mapped_column(Integer, nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    titulo: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    __table_args__ = (
        Index(
            "ix_fecha_academica_tenant_materia_cohorte_tipo_num",
            "tenant_id",
            "materia_id",
            "cohorte_id",
            "tipo",
            "numero_instancia",
            unique=True,
        ),
        Index("ix_fecha_academica_tenant_deleted", "tenant_id", "deleted_at"),
    )
