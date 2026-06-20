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
    facturante: bool = False
    created_at: datetime
    updated_at: datetime


class PerfilUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # TODO: (FEAT) Auditoría backend/frontend 2026-06-19: F11.1 / C-20 piden
    # editar modalidad de cobro (factura/liquidación). El modelo `Usuario`
    # tiene `facturante`, pero el payload de update no permite modificarlo.

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
