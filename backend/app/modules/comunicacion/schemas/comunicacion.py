"""Pydantic schemas for Comunicacion."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.comunicacion.models.comunicacion import (
    ComunicacionEstado,
    InvalidStateTransitionError,
)


class ComunicacionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asunto: str = Field(..., min_length=1, max_length=500)
    cuerpo: str = Field(..., min_length=1)
    destinatario: EmailStr
    lote_id: UUID | None = None


class ComunicacionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asunto: str | None = Field(None, min_length=1, max_length=500)
    cuerpo: str | None = Field(None, min_length=1)
    destinatario: EmailStr | None = None


class ComunicacionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    asunto: str
    cuerpo: str
    destinatario: str
    estado: ComunicacionEstado
    lote_id: UUID | None
    error_detail: str | None
    enviado_at: datetime | None
    retry_count: int
    created_at: datetime
    updated_at: datetime


class ComunicacionStateTransition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estado: ComunicacionEstado

    def validate_transition(self, current: ComunicacionEstado) -> None:
        InvalidStateTransitionError  # noqa: B018
        from app.modules.comunicacion.models.comunicacion import validate_transition
        validate_transition(current, self.estado)


class LoteStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lote_id: UUID
    tenant_id: UUID
    total: int
    pendientes: int
    enviando: int
    enviados: int
    errores: int
    cancelados: int


class LotePendienteResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lote_id: UUID
    tenant_id: UUID
    total: int
    pendientes: int
    enviando: int
    enviados: int
    errores: int
    cancelados: int
    asunto: str
    cuerpo: str
    destinatarios: list[str]
