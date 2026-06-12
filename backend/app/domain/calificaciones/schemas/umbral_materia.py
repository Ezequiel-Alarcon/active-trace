"""UmbralMateria Pydantic schemas (C-10).

Request/response DTOs. Todos usan extra='forbid'.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UmbralMateriaBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    asignacion_id: UUID | None = None
    umbral_pct: int = 60
    conjunto_aprobado: list[str] | None = None


class UmbralMateriaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    asignacion_id: UUID | None = None
    umbral_pct: int = 60
    conjunto_aprobado: list[str] | None = None


class UmbralMateriaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    umbral_pct: int | None = None
    conjunto_aprobado: list[str] | None = None


class UmbralMateriaRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    materia_id: UUID
    asignacion_id: UUID | None
    umbral_pct: int
    conjunto_aprobado: list[str] | None
    created_at: datetime
    updated_at: datetime