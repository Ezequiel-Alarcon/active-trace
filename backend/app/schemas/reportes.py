"""Schemas para reportes de alumnos (C-11)."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ActividadEstado(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asignacion_id: UUID | None
    asignacion_nombre: str | None
    estado: str
    nota: float | int | str | list | None
    umbral_pct: int


class AlumnoReporte(BaseModel):
    model_config = ConfigDict(extra="forbid")

    usuario_id: UUID
    nombre: str
    email: str
    actividades: list[ActividadEstado]


class ReporteMateriaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    materia_nombre: str
    cohorte_id: UUID
    cohorte_nombre: str
    total_alumnos: int
    alumnos: list[AlumnoReporte]


class NotasFinalesEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    materia_nombre: str
    total_alumnos: int
    aprobados: int
    tasa_aprobacion: float
    nota_promedio_global: float | None


class NotasFinalesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int
    limit: int
    offset: int
    notas: list[NotasFinalesEntry]