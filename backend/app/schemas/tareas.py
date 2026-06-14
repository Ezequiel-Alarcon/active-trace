from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TareaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID | None = None
    asignado_a: UUID
    descripcion: str = Field(min_length=1)
    contexto_id: UUID | None = None


class TareaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estado: str | None = None
    descripcion: str | None = Field(default=None, min_length=1)


class TareaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    materia_id: UUID | None = None
    asignado_a: UUID
    asignado_por: UUID
    estado: str
    descripcion: str
    contexto_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class TareaListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[TareaResponse]
    total: int
    page: int
    per_page: int


class ComentarioCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    texto: str = Field(min_length=1)


class ComentarioResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tarea_id: UUID
    autor_id: UUID
    texto: str
    created_at: datetime
    updated_at: datetime


class ComentarioListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ComentarioResponse]
    total: int
    page: int
    per_page: int
