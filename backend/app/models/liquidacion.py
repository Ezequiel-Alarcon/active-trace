from __future__ import annotations

import enum
from datetime import date as DateType
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, Enum, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TenantScopedMixin


class LiquidacionEstado(str, enum.Enum):
    ABIERTA = "Abierta"
    CERRADA = "Cerrada"


class FacturaEstado(str, enum.Enum):
    PENDIENTE = "Pendiente"
    ABONADA = "Abonada"


class PlusCategoria(Base):
    __tablename__ = "plus_categoria"

    grupo: Mapped[str] = mapped_column(String(32), primary_key=True)
    descripcion: Mapped[str] = mapped_column(String(255), nullable=False)


class SalarioBase(Base, TenantScopedMixin):
    __tablename__ = "salario_base"

    rol: Mapped[str] = mapped_column(String(64), nullable=False)
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    desde: Mapped[DateType] = mapped_column(Date, nullable=False)
    hasta: Mapped[DateType | None] = mapped_column(Date, nullable=True)

    __table_args__ = (
        Index("ix_salario_base_tenant_rol", "tenant_id", "rol"),
        Index("ix_salario_base_tenant_deleted", "tenant_id", "deleted_at"),
    )


class SalarioPlus(Base, TenantScopedMixin):
    __tablename__ = "salario_plus"

    grupo: Mapped[str] = mapped_column(String(32), ForeignKey("plus_categoria.grupo"), nullable=False)
    rol: Mapped[str] = mapped_column(String(64), nullable=False)
    descripcion: Mapped[str] = mapped_column(String(255), nullable=False)
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    desde: Mapped[DateType] = mapped_column(Date, nullable=False)
    hasta: Mapped[DateType | None] = mapped_column(Date, nullable=True)

    __table_args__ = (
        Index("ix_salario_plus_tenant_grupo_rol", "tenant_id", "grupo", "rol"),
        Index("ix_salario_plus_tenant_deleted", "tenant_id", "deleted_at"),
    )


class Liquidacion(Base, TenantScopedMixin):
    __tablename__ = "liquidacion"

    usuario_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    rol: Mapped[str] = mapped_column(String(64), nullable=False)
    cohorte_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    periodo: Mapped[str] = mapped_column(String(7), nullable=False)
    monto_base: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    monto_plus: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    comisiones: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    es_nexo: Mapped[bool] = mapped_column(nullable=False, default=False, server_default="false")
    excluido_por_factura: Mapped[bool] = mapped_column(nullable=False, default=False, server_default="false")
    estado: Mapped[LiquidacionEstado] = mapped_column(
        Enum(LiquidacionEstado, name="liquidacion_estado", values_callable=lambda x: [m.value for m in x]),
        nullable=False,
        default=LiquidacionEstado.ABIERTA,
    )

    __table_args__ = (
        Index("ix_liquidacion_tenant_periodo", "tenant_id", "cohorte_id", "periodo"),
        Index("ix_liquidacion_tenant_usuario", "tenant_id", "usuario_id"),
        Index("ix_liquidacion_tenant_deleted", "tenant_id", "deleted_at"),
    )


class Factura(Base, TenantScopedMixin):
    __tablename__ = "factura"

    usuario_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    periodo: Mapped[str] = mapped_column(String(7), nullable=False)
    detalle: Mapped[str] = mapped_column(String(1000), nullable=False)
    referencia_archivo: Mapped[str] = mapped_column(String(512), nullable=False)
    tamano_kb: Mapped[int] = mapped_column(Integer, nullable=False)
    estado: Mapped[FacturaEstado] = mapped_column(
        Enum(FacturaEstado, name="factura_estado", values_callable=lambda x: [m.value for m in x]),
        nullable=False,
        default=FacturaEstado.PENDIENTE,
    )
    cargada_at: Mapped[DateType] = mapped_column(Date, nullable=False)
    abonada_at: Mapped[DateType | None] = mapped_column(Date, nullable=True)

    __table_args__ = (
        Index("ix_factura_tenant_usuario_periodo", "tenant_id", "usuario_id", "periodo"),
        Index("ix_factura_tenant_estado", "tenant_id", "estado"),
        Index("ix_factura_tenant_deleted", "tenant_id", "deleted_at"),
    )
