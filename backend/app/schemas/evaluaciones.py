"""Evaluaciones Pydantic schemas (C-14).

Request/response DTOs for Coloquio/Evaluacion endpoints.
All schemas use extra='forbid' per project convention.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DiaSlotSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fecha: date
    cupos: int


class EvaluacionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    cohorte_id: UUID
    instancia: str
    tipo: str = "Coloquio"
    fecha_inicio: date
    dias_disponibles: int
    cupos: int


class EvaluacionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    materia_id: UUID
    cohorte_id: UUID
    tipo: str
    instancia: str
    dias_disponibles: int
    cupos: int
    fecha_inicio: date
    dias: list[DiaSlotSchema]
    estado: str
    created_at: datetime
    updated_at: datetime


class EvaluacionMetricsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    materia_id: UUID
    instancia: str
    estado: str
    convocados: int
    reservas_activas: int
    cupos_libres: int


class EvaluacionListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evaluaciones: list[EvaluacionMetricsResponse]


class ImportarAlumnosRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alumno_ids: list[UUID]


class ImportarAlumnosResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    importados: int
    saltados: int


class ReservaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fecha: date


class ReservaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    evaluacion_id: UUID
    alumno_id: UUID
    fecha_reserva: date
    estado: str
    created_at: datetime
    updated_at: datetime


class MisReservasItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reserva_id: UUID
    evaluacion_id: UUID
    materia: str | None
    instancia: str
    fecha_reserva: date
    estado: str


class ResultadoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alumno_id: UUID
    nota_final: str


class ResultadoResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    evaluacion_id: UUID
    alumno_id: UUID
    nota_final: str | None
    created_at: datetime
    updated_at: datetime


class ResultadoConAlumno(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    alumno_id: UUID
    alumno_nombre: str | None
    nota_final: str | None
    estado_reserva: str | None


class ColoquioMetricsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_convocados: int
    total_reservas_activas: int
    total_cupos_libres: int
    instancias_activas: int