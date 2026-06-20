"""Guardias Pydantic schemas (C-18 §4).

Request/response DTOs for Guardia endpoints.
All schemas use extra='forbid' per project convention.
tutor_id is never accepted from the client — it comes from the session.
"""

from __future__ import annotations

from datetime import date, datetime, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class GuardiaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    cohorte_id: UUID
    fecha: date
    hora_inicio: time
    hora_fin: time
    titulo: str | None = None
    observaciones: str | None = None


class GuardiaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fecha: date | None = None
    hora_inicio: time | None = None
    hora_fin: time | None = None
    titulo: str | None = None
    observaciones: str | None = None


class GuardiaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # TODO: (REVIEW) Auditoría backend/frontend 2026-06-19: la pantalla de
    # historial de guardias espera responsable, materia, carrera/cohorte,
    # horario, estado, comentarios y fecha de registro. Este DTO solo expone
    # IDs + `tutor_nombre`; faltan `estado` y datos expandidos para renderizar
    # la tabla sin round-trips adicionales.

    id: UUID
    tenant_id: UUID
    tutor_id: UUID
    tutor_nombre: str | None = None
    materia_id: UUID
    cohorte_id: UUID
    fecha: date
    hora_inicio: time
    hora_fin: time
    titulo: str | None
    observaciones: str | None
    created_at: datetime
    updated_at: datetime
