"""`evaluacion` table — evaluación formal (parcial, coloquio, recuperatorio).

E14 from KB: Evaluacion, ReservaEvaluacion, ResultadoEvaluacion.
Each evaluacion has a JSONB `dias` array with {fecha, cupos} objects
auto-generated from dias_disponibles + fecha_inicio + cupos.
"""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Date, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TenantScopedMixin


class EvaluacionTipo(str, enum.Enum):
    PARCIAL = "Parcial"
    TP = "TP"
    COLOQUIO = "Coloquio"
    RECUPERATORIO = "Recuperatorio"


class EvaluacionEstado(str, enum.Enum):
    ABIERTA = "Abierta"
    CERRADA = "Cerrada"


class ReservaEstado(str, enum.Enum):
    ACTIVA = "Activa"
    CANCELADA = "Cancelada"


class Evaluacion(Base, TenantScopedMixin):
    __tablename__ = "evaluacion"

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
    tipo: Mapped[EvaluacionTipo] = mapped_column(
        Enum(EvaluacionTipo, name="evaluacion_tipo", values_callable=lambda x: [m.value for m in x]),
        nullable=False,
        default=EvaluacionTipo.COLOQUIO,
    )
    instancia: Mapped[str] = mapped_column(String(255), nullable=False)
    dias_disponibles: Mapped[int] = mapped_column(Integer, nullable=False)
    cupos: Mapped[int] = mapped_column(Integer, nullable=False)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    dias: Mapped[list] = mapped_column(JSONB, nullable=False)
    estado: Mapped[EvaluacionEstado] = mapped_column(
        Enum(EvaluacionEstado, name="evaluacion_estado", values_callable=lambda x: [m.value for m in x]),
        nullable=False,
        default=EvaluacionEstado.ABIERTA,
    )

    __table_args__ = (
        Index("ix_evaluacion_tenant_materia", "tenant_id", "materia_id"),
        Index("ix_evaluacion_tenant_cohorte", "tenant_id", "cohorte_id"),
        Index("ix_evaluacion_tenant_deleted", "tenant_id", "deleted_at"),
        Index("ix_evaluacion_tenant_estado", "tenant_id", "estado"),
    )


class ReservaEvaluacion(Base, TenantScopedMixin):
    __tablename__ = "reserva_evaluacion"

    evaluacion_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("evaluacion.id", ondelete="CASCADE"),
        nullable=False,
    )
    alumno_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("usuario.id", ondelete="RESTRICT"),
        nullable=False,
    )
    fecha_reserva: Mapped[date] = mapped_column(Date, nullable=False)
    estado: Mapped[ReservaEstado] = mapped_column(
        Enum(ReservaEstado, name="reserva_estado", values_callable=lambda x: [m.value for m in x]),
        nullable=False,
        default=ReservaEstado.ACTIVA,
    )

    __table_args__ = (
        Index("ix_reserva_evaluacion_tenant_evaluacion", "tenant_id", "evaluacion_id"),
        Index("ix_reserva_evaluacion_tenant_alumno", "tenant_id", "alumno_id"),
        Index("ix_reserva_evaluacion_tenant_deleted", "tenant_id", "deleted_at"),
        Index("ix_reserva_evaluacion_unique_active", "tenant_id", "evaluacion_id", "alumno_id", unique=True),
    )


class ResultadoEvaluacion(Base, TenantScopedMixin):
    __tablename__ = "resultado_evaluacion"

    evaluacion_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("evaluacion.id", ondelete="CASCADE"),
        nullable=False,
    )
    alumno_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("usuario.id", ondelete="RESTRICT"),
        nullable=False,
    )
    nota_final: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_resultado_evaluacion_tenant_evaluacion", "tenant_id", "evaluacion_id"),
        Index("ix_resultado_evaluacion_tenant_alumno", "tenant_id", "alumno_id"),
        Index("ix_resultado_evaluacion_tenant_deleted", "tenant_id", "deleted_at"),
        Index("ix_resultado_evaluacion_unique", "tenant_id", "evaluacion_id", "alumno_id", unique=True),
    )