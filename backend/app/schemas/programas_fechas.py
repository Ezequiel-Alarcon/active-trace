"""Programas y Fechas Academicas Pydantic schemas (C-17 §2).

Request/response DTOs for programa_materia and fecha_academica endpoints.
All schemas use extra='forbid' per project convention.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# ── ProgramaMateria ───────────────────────────────────────────────────

class ProgramaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    carrera_id: UUID
    cohorte_id: UUID
    titulo: str
    referencia_archivo: str | None = None


class ProgramaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titulo: str | None = None
    referencia_archivo: str | None = None


class ProgramaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    materia_id: UUID
    carrera_id: UUID
    cohorte_id: UUID
    titulo: str
    referencia_archivo: str | None
    created_at: datetime
    updated_at: datetime


# ── FechaAcademica ────────────────────────────────────────────────────

class FechaAcademicaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    cohorte_id: UUID
    tipo: Literal["Parcial", "TP", "Coloquio"]
    numero_instancia: int
    fecha: date
    titulo: str | None = None
    descripcion: str | None = None


class FechaAcademicaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fecha: date | None = None
    titulo: str | None = None
    descripcion: str | None = None


class FechaAcademicaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    materia_id: UUID
    cohorte_id: UUID
    tipo: str
    numero_instancia: int
    fecha: date
    titulo: str | None
    descripcion: str | None
    created_at: datetime
    updated_at: datetime


# ── Fragmento LMS ─────────────────────────────────────────────────────

class FragmentoLmsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    html: str
