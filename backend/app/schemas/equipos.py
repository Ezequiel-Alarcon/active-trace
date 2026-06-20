"""Equipos docentes Pydantic schemas (C-08).

Request/response DTOs para los endpoints batch de equipos: asignacion masiva,
clonar entre cohortes, vigencia general y export CSV.
Todos los schemas usan extra='forbid' segun la convencion del proyecto.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# ── EquipoAsignacionResponse (extiende AsignacionResponse) ─────────────

class EquipoAsignacionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # TODO: (REVIEW) Auditoría backend/frontend 2026-06-19: este DTO no cubre
    # la grilla documentada para "Mis Equipos". Faltan campos explícitos para
    # carrera, cohorte, materia/código y comisiones; hoy el frontend tendría
    # que inferir demasiado desde `nombre_contexto`.

    id: UUID
    tenant_id: UUID
    usuario_id: UUID
    rol_id: UUID
    contexto_tipo: str
    contexto_id: UUID | None = None
    responsable_id: UUID | None = None
    desde: date
    hasta: date | None = None
    estado_vigencia: str
    created_at: datetime
    updated_at: datetime
    nombre_usuario: str
    apellidos_usuario: str
    email_usuario: str
    nombre_rol: str
    nombre_contexto: str


# ── Asignacion Masiva ──────────────────────────────────────────────────

class AsignacionMasivaRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    usuarios_ids: list[UUID]
    rol_id: UUID
    contexto_tipo: str
    contexto_id: UUID | None = None
    desde: date
    hasta: date | None = None
    responsable_id: UUID | None = None


class AsignacionFallida(BaseModel):
    model_config = ConfigDict(extra="forbid")

    usuario_id: UUID | None = None
    motivo: str


class AsignacionMasivaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    creadas: list[EquipoAsignacionResponse]
    fallidas: list[AsignacionFallida]


# ── Clonar Equipo ──────────────────────────────────────────────────────

class ClonarEquipoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cohorte_origen_id: UUID
    cohorte_destino_id: UUID
    desde: date
    hasta: date | None = None


class ClonadoFallido(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asignacion_origen_id: UUID
    motivo: str


class ClonarEquipoResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    creadas: int
    omitidas: int
    fallidas: list[ClonadoFallido]


# ── Vigencia Equipo ────────────────────────────────────────────────────

class VigenciaEquipoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    cohorte_id: UUID
    rol_id: UUID | None = None
    desde: date
    hasta: date | None = None


class VigenciaEquipoResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actualizadas: int
