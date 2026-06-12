"""Padron Pydantic schemas (C-09).

Request/response DTOs para el módulo de padrón de alumnos.
Todos los schemas usan extra='forbid' según la convención del proyecto.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EntradaPadronCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    usuario_id: UUID | None = None
    nombre: str
    apellidos: str
    email: str
    comision: str | None = None
    regional: str | None = None


class EntradaPadronResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    version_id: UUID
    tenant_id: UUID
    usuario_id: UUID | None
    nombre: str
    apellidos: str
    email: str
    comision: str | None
    regional: str | None
    created_at: datetime
    updated_at: datetime


class VersionPadronCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    cohorte_id: UUID
    entradas: list[EntradaPadronCreate]


class VersionPadronResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    materia_id: UUID
    cohorte_id: UUID
    cargado_por: UUID
    cargado_at: datetime
    activa: bool
    created_at: datetime
    updated_at: datetime
    entradas: list[EntradaPadronResponse] | None = None


class PadronPreviewRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str
    apellidos: str
    email: str
    comision: str | None
    regional: str | None
    matched_usuario_id: UUID | None


class PadronPreviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rows: list[PadronPreviewRow]
    total: int
    filename: str