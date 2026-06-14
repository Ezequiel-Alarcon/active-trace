from __future__ import annotations

import enum
from uuid import UUID

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TenantScopedMixin


class AlcanceAviso(str, enum.Enum):
    GLOBAL = "Global"
    POR_MATERIA = "PorMateria"
    POR_COHORTE = "PorCohorte"
    POR_ROL = "PorRol"


class SeveridadAviso(str, enum.Enum):
    INFO = "Info"
    ADVERTENCIA = "Advertencia"
    CRITICO = "Crítico"


class Aviso(Base, TenantScopedMixin):
    __tablename__ = "aviso"

    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    cuerpo: Mapped[str] = mapped_column(Text, nullable=False)
    alcance: Mapped[AlcanceAviso] = mapped_column(
        Enum(AlcanceAviso, name="alcance_aviso", values_callable=lambda x: [m.value for m in x]),
        nullable=False,
    )
    severidad: Mapped[SeveridadAviso] = mapped_column(
        Enum(SeveridadAviso, name="severidad_aviso", values_callable=lambda x: [m.value for m in x]),
        nullable=False,
        default=SeveridadAviso.INFO,
    )
    rol_destino: Mapped[str | None] = mapped_column(String(64), nullable=True)
    materia_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    cohorte_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    inicio_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fin_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    requiere_ack: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        Index("ix_aviso_tenant", "tenant_id"),
        Index("ix_aviso_tenant_deleted", "tenant_id", "deleted_at"),
        Index("ix_aviso_tenant_alcance", "tenant_id", "alcance"),
        Index("ix_aviso_tenant_activo", "tenant_id", "activo", "inicio_en", "fin_en"),
    )


class AcknowledgmentAviso(Base, TenantScopedMixin):
    __tablename__ = "acknowledgment_aviso"

    aviso_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    usuario_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)

    __table_args__ = (
        Index("ix_ack_aviso_tenant_aviso", "tenant_id", "aviso_id"),
        Index("ix_ack_aviso_tenant_usuario", "tenant_id", "usuario_id"),
        Index(
            "ix_ack_aviso_tenant_aviso_usuario",
            "tenant_id",
            "aviso_id",
            "usuario_id",
            unique=True,
        ),
    )
