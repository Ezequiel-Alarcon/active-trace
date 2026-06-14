"""`cohorte` table — cohortes académicas por carrera y tenant (C-06).

Cada cohorte pertenece a una carrera y a un tenant. La unicidad es
compuesta por (tenant_id, carrera_id, nombre). La cohorte tiene un
rango de vigencia (vig_desde, vig_hasta); vig_hasta = NULL significa
cohorte abierta.
"""

from __future__ import annotations

import enum
from datetime import date
from uuid import UUID

from sqlalchemy import Date, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TenantScopedMixin


class CohorteEstado(str, enum.Enum):
    ACTIVA = "Activa"
    INACTIVA = "Inactiva"


class Cohorte(Base, TenantScopedMixin):
    __tablename__ = "cohorte"

    carrera_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("carrera.id", ondelete="RESTRICT"),
        nullable=False,
    )
    nombre: Mapped[str] = mapped_column(String(128), nullable=False)
    anio: Mapped[int] = mapped_column(Integer, nullable=False)
    vig_desde: Mapped[date] = mapped_column(Date, nullable=False)
    vig_hasta: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    estado: Mapped[CohorteEstado] = mapped_column(
        Enum(CohorteEstado, name="cohorte_estado", values_callable=lambda x: [m.value for m in x]),
        nullable=False,
        default=CohorteEstado.ACTIVA,
    )

    __table_args__ = (
        Index("ix_cohorte_tenant_carrera_nombre", "tenant_id", "carrera_id", "nombre", unique=True),
        Index("ix_cohorte_tenant_deleted", "tenant_id", "deleted_at"),
    )
