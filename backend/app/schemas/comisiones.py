"""Schemas for derived commission listing."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ComisionRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    materia_id: UUID
    materia_nombre: str
    cohorte_id: UUID
    cohorte_nombre: str
