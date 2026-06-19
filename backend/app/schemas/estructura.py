"""Estructura academica Pydantic schemas (C-06 §2).

Request/response DTOs for carrera, cohorte y materia endpoints.
All schemas use extra='forbid' per project convention.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# ── Carrera ──────────────────────────────────────────────────────────

class CarreraCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    codigo: str
    nombre: str
    plus_grupo: str | None = None


class CarreraUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    codigo: str | None = None
    nombre: str | None = None
    estado: str | None = None
    plus_grupo: str | None = None


class CarreraResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    codigo: str
    nombre: str
    estado: str
    created_at: datetime
    updated_at: datetime


# ── Cohorte ──────────────────────────────────────────────────────────

class CohorteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    carrera_id: UUID
    nombre: str
    anio: int
    vig_desde: date
    vig_hasta: date | None = None


class CohorteUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str | None = None
    anio: int | None = None
    vig_desde: date | None = None
    vig_hasta: date | None = None
    estado: str | None = None


class CohorteResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    carrera_id: UUID
    nombre: str
    anio: int
    vig_desde: date
    vig_hasta: date | None
    estado: str
    created_at: datetime
    updated_at: datetime


# ── Materia ──────────────────────────────────────────────────────────

class MateriaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    codigo: str
    nombre: str
    plus_grupo: str | None = None


class MateriaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    codigo: str | None = None
    nombre: str | None = None
    estado: str | None = None
    plus_grupo: str | None = None


class MateriaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    codigo: str
    nombre: str
    estado: str
    plus_grupo: str | None = None
    created_at: datetime
    updated_at: datetime
