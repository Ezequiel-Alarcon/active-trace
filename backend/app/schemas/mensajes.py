from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MensajeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asunto: str
    cuerpo: str
    destinatario_id: UUID
    hilo_id: UUID | None = None


class MensajeReply(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asunto: str
    cuerpo: str


class MensajeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    asunto: str
    cuerpo: str
    remitente_id: UUID
    destinatario_id: UUID
    hilo_id: UUID
    padre_id: UUID | None = None
    leido_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class InboxThreadItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hilo_id: UUID
    remitente_id: UUID
    destinatario_id: UUID
    ultimo_asunto: str
    ultimo_cuerpo: str
    leido: bool
    ultima_actividad: datetime
