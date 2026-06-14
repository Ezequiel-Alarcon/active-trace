from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PerfilResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    nombre: str
    apellidos: str
    email: str
    dni: str
    cuil: str
    cbu: str
    alias_cbu: str | None = None
    banco: str | None = None
    regional: str | None = None
    legajo: str | None = None
    legajo_profesional: str | None = None
    fecha_nacimiento: date | None = None
    genero: str | None = None
    observaciones: str | None = None
    created_at: datetime
    updated_at: datetime


class PerfilUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str | None = None
    apellidos: str | None = None
    email: str | None = None
    dni: str | None = None
    cbu: str | None = None
    alias_cbu: str | None = None
    banco: str | None = None
    regional: str | None = None
    legajo: str | None = None
    legajo_profesional: str | None = None
    fecha_nacimiento: date | None = None
    genero: str | None = None
    observaciones: str | None = None
