"""`slot_encuentro` table — plantilla de encuentro recurrente (C-18).

Define el dia de la semana y rango horario fijo de un encuentro, junto
con la cantidad de semanas que se repite. Al crear un slot se generan
automaticamente las instancias correspondientes.
"""

from __future__ import annotations

import enum
from datetime import date, datetime, time
from uuid import UUID

from sqlalchemy import Date, Enum, ForeignKey, Index, Integer, String, Time
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TenantScopedMixin


class DiaSemana(int, enum.Enum):
    LUNES = 0
    MARTES = 1
    MIERCOLES = 2
    JUEVES = 3
    VIERNES = 4
    SABADO = 5
    DOMINGO = 6


class SlotEncuentro(Base, TenantScopedMixin):
    __tablename__ = "slot_encuentro"

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
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    dia_semana: Mapped[int] = mapped_column(Integer, nullable=False)
    hora_inicio: Mapped[time] = mapped_column(Time, nullable=False)
    hora_fin: Mapped[time] = mapped_column(Time, nullable=False)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    cant_semanas: Mapped[int] = mapped_column(Integer, nullable=False)
    meet_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    __table_args__ = (
        Index("ix_slot_encuentro_tenant_materia_cohorte", "tenant_id", "materia_id", "cohorte_id"),
        Index("ix_slot_encuentro_tenant_deleted", "tenant_id", "deleted_at"),
    )
