"""Schemas para analisis de atrasados y rankings (C-11)."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AlumnoAtrasado(BaseModel):
    model_config = ConfigDict(extra="forbid")

    usuario_id: UUID
    email: str
    nombre: str
    materia_id: UUID
    materia_nombre: str
    asignacion_id: UUID | None
    asignacion_nombre: str | None
    estado: str
    nota_actual: float | int | str | list | None
    umbral_pct: int


class AtrasadosResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int
    limit: int
    offset: int
    alumnos: list[AlumnoAtrasado]


class RankingEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    posicion: int
    usuario_id: UUID
    nombre: str
    email: str
    cantidad_aprobadas: int
    cantidad_totales: int
    nota_promedio: float | None


class RankingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    materia_nombre: str
    rankings: list[RankingEntry]