"""`instancia_encuentro` table — ocurrencia concreta de un encuentro (C-18).

Puede pertenecer a un SlotEncuentro (slot_id) o ser un encuentro unico
(slot_id=NULL). El estado se gestiona como enum de tres valores.
"""

from __future__ import annotations

import enum
from datetime import date, datetime, time
from uuid import UUID

from sqlalchemy import Date, Enum, ForeignKey, Index, String, Text, Time
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TenantScopedMixin


class EstadoEncuentro(str, enum.Enum):
    PROGRAMADO = "Programado"
    REALIZADO = "Realizado"
    CANCELADO = "Cancelado"


class InstanciaEncuentro(Base, TenantScopedMixin):
    __tablename__ = "instancia_encuentro"

    slot_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("slot_encuentro.id", ondelete="SET NULL"),
        nullable=True,
    )
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
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    hora_inicio: Mapped[time] = mapped_column(Time, nullable=False)
    hora_fin: Mapped[time] = mapped_column(Time, nullable=False)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    estado: Mapped[EstadoEncuentro] = mapped_column(
        Enum(EstadoEncuentro, name="estado_encuentro", values_callable=lambda x: [m.value for m in x]),
        nullable=False,
        default=EstadoEncuentro.PROGRAMADO,
    )
    meet_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    comentario: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_instancia_encuentro_tenant_materia_cohorte", "tenant_id", "materia_id", "cohorte_id"),
        Index("ix_instancia_encuentro_tenant_slot", "tenant_id", "slot_id"),
        Index("ix_instancia_encuentro_tenant_deleted", "tenant_id", "deleted_at"),
    )
