"""Schemas para exportacion de TPs sin corregir (C-11)."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TpsSinCorregirEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    usuario_id: UUID | None
    materia_id: UUID
    materia_nombre: str | None = None


class TpsSinCorregirResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int
    alumnos: list[dict]