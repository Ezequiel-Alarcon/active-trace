"""Calificacion Pydantic schemas (C-10).

Request/response DTOs. Todos usan extra='forbid'.
"""

from __future__ import annotations

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CalificacionOrigen(str, Enum):
    IMPORTADO = "Importado"
    MANUAL = "Manual"


class CalificacionBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    usuario_id: UUID
    asignacion_id: UUID | None = None
    nota: Any = None
    origen: CalificacionOrigen


class CalificacionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    usuario_id: UUID
    asignacion_id: UUID | None = None
    nota: Any = None
    origen: CalificacionOrigen = CalificacionOrigen.MANUAL


class CalificacionPreviewRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    usuario_id: UUID | None
    materia_id: UUID
    asignacion_id: UUID | None
    nota: Any
    valid: bool
    warnings: list[str]


class CalificacionPreviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    preview_token: str
    rows: list[CalificacionPreviewRow]
    total: int
    filename: str


class CalificacionConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    preview_token: str


class CalificacionConfirmResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    persisted: int
    skipped: int
    failed: int


class CalificacionRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    materia_id: UUID
    usuario_id: UUID
    asignacion_id: UUID | None
    version_padron_id: UUID | None
    nota: Any
    origen: CalificacionOrigen
    import_batch_id: UUID | None
    created_at: datetime
    updated_at: datetime
    aprobado: bool | None = None