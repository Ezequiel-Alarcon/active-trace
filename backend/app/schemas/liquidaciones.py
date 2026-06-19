from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SalarioBaseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rol: str
    monto: Decimal
    desde: date
    hasta: date | None = None


class SalarioPlusCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    grupo: str
    rol: str
    descripcion: str
    monto: Decimal
    desde: date
    hasta: date | None = None


class SalarioResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    rol: str
    monto: Decimal
    desde: date
    hasta: date | None = None
    created_at: datetime
    updated_at: datetime


class SalarioPlusResponse(SalarioResponse):
    grupo: str
    descripcion: str


class LiquidacionCalcularRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cohorte_id: UUID
    periodo: str = Field(pattern=r"^\d{4}-\d{2}$")


class LiquidacionCerrarRequest(LiquidacionCalcularRequest):
    confirmar: bool


class LiquidacionItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    usuario_id: UUID
    rol: str
    cohorte_id: UUID
    periodo: str
    monto_base: Decimal
    monto_plus: Decimal
    total: Decimal
    comisiones: list[dict]
    es_nexo: bool
    excluido_por_factura: bool
    estado: str


class LiquidacionKpis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_sin_factura: Decimal
    total_facturantes: Decimal


class LiquidacionSegmentos(BaseModel):
    model_config = ConfigDict(extra="forbid")

    general_total: Decimal
    nexo_total: Decimal
    facturantes_total: Decimal


class LiquidacionResultado(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cohorte_id: UUID
    periodo: str
    items: list[LiquidacionItem]
    kpis: LiquidacionKpis
    segmentos: LiquidacionSegmentos


class LiquidacionCierreResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cohorte_id: UUID
    periodo: str
    filas_afectadas: int


class FacturaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    usuario_id: UUID
    periodo: str = Field(pattern=r"^\d{4}-\d{2}$")
    detalle: str
    referencia_archivo: str
    tamano_kb: int


class FacturaPagoConfirm(BaseModel):
    model_config = ConfigDict(extra="forbid")
    confirmar: bool


class FacturaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    usuario_id: UUID
    periodo: str
    detalle: str
    referencia_archivo: str
    tamano_kb: int
    estado: str
    cargada_at: date
    abonada_at: date | None = None
    created_at: datetime
    updated_at: datetime


class FacturaDescargaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    referencia_archivo: str
