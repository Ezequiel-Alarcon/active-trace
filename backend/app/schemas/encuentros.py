"""Encuentros Pydantic schemas (C-18 §3).

Request/response DTOs for SlotEncuentro and InstanciaEncuentro endpoints.
All schemas use extra='forbid' per project convention.
"""

from __future__ import annotations

from datetime import date, datetime, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ── SlotEncuentro ─────────────────────────────────────────────────────

class SlotEncuentroCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    cohorte_id: UUID
    titulo: str
    dia_semana: int = Field(ge=0, le=6)
    hora_inicio: time
    hora_fin: time
    fecha_inicio: date
    cant_semanas: int = Field(ge=1, le=52)
    meet_url: str | None = None
    video_url: str | None = None


class SlotEncuentroUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titulo: str | None = None
    dia_semana: int | None = Field(None, ge=0, le=6)
    hora_inicio: time | None = None
    hora_fin: time | None = None
    meet_url: str | None = None
    video_url: str | None = None


class InstanciaEncuentroBrief(BaseModel):
    """Instancia nested inside SlotEncuentroResponse."""
    model_config = ConfigDict(extra="forbid")

    id: UUID
    slot_id: UUID | None
    materia_id: UUID
    cohorte_id: UUID
    fecha: date
    hora_inicio: time
    hora_fin: time
    titulo: str
    estado: str
    meet_url: str | None
    video_url: str | None
    comentario: str | None
    created_at: datetime


class SlotEncuentroResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    materia_id: UUID
    cohorte_id: UUID
    titulo: str
    dia_semana: int
    hora_inicio: time
    hora_fin: time
    fecha_inicio: date
    cant_semanas: int
    meet_url: str | None
    video_url: str | None
    created_at: datetime
    updated_at: datetime
    instancias: list[InstanciaEncuentroBrief] = Field(default_factory=list)


# ── InstanciaEncuentro ─────────────────────────────────────────────────

class InstanciaEncuentroCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    cohorte_id: UUID
    fecha: date
    hora_inicio: time
    hora_fin: time
    titulo: str
    meet_url: str | None = None
    video_url: str | None = None
    comentario: str | None = None


class InstanciaEncuentroUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estado: str | None = None
    fecha: date | None = None
    hora_inicio: time | None = None
    hora_fin: time | None = None
    titulo: str | None = None
    meet_url: str | None = None
    video_url: str | None = None
    comentario: str | None = None


class InstanciaEncuentroResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    slot_id: UUID | None
    materia_id: UUID
    cohorte_id: UUID
    fecha: date
    hora_inicio: time
    hora_fin: time
    titulo: str
    estado: str
    meet_url: str | None
    video_url: str | None
    comentario: str | None
    created_at: datetime
    updated_at: datetime
