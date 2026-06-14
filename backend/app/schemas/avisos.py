from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AvisoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titulo: str
    cuerpo: str
    alcance: str
    severidad: str = "Info"
    rol_destino: str | None = None
    materia_id: UUID | None = None
    cohorte_id: UUID | None = None
    inicio_en: datetime | None = None
    fin_en: datetime | None = None
    orden: int = 0
    activo: bool = True
    requiere_ack: bool = False


class AvisoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titulo: str | None = None
    cuerpo: str | None = None
    alcance: str | None = None
    severidad: str | None = None
    rol_destino: str | None = None
    materia_id: UUID | None = None
    cohorte_id: UUID | None = None
    inicio_en: datetime | None = None
    fin_en: datetime | None = None
    orden: int | None = None
    activo: bool | None = None
    requiere_ack: bool | None = None


class AvisoResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    titulo: str
    cuerpo: str
    alcance: str
    severidad: str
    rol_destino: str | None = None
    materia_id: UUID | None = None
    cohorte_id: UUID | None = None
    inicio_en: datetime | None = None
    fin_en: datetime | None = None
    orden: int
    activo: bool
    requiere_ack: bool
    created_at: datetime
    updated_at: datetime


class AvisoListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[AvisoResponse]
    total: int
    page: int
    per_page: int


class AcknowledgmentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    aviso_id: UUID
    usuario_id: UUID
    created_at: datetime


class AcknowledgmentStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int
    user_acknowledged: bool
    requiere_ack: bool
