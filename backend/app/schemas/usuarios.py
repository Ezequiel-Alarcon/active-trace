"""Usuario y Asignacion Pydantic schemas (C-07).

Request/response DTOs para los endpoints de admin/usuarios y asignaciones.
Todos los schemas usan extra='forbid' segun la convencion del proyecto.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# ── Usuario ───────────────────────────────────────────────────────────

class UsuarioCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID | None = None
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


class UsuarioUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str | None = None
    apellidos: str | None = None
    email: str | None = None
    dni: str | None = None
    cuil: str | None = None
    cbu: str | None = None
    alias_cbu: str | None = None
    banco: str | None = None
    regional: str | None = None
    legajo: str | None = None
    legajo_profesional: str | None = None
    fecha_nacimiento: date | None = None
    genero: str | None = None
    observaciones: str | None = None


class UsuarioResponse(BaseModel):
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


class UsuarioListItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    nombre: str
    apellidos: str
    email: str
    legajo: str | None = None
    legajo_profesional: str | None = None
    created_at: datetime
    updated_at: datetime


# ── Asignacion ────────────────────────────────────────────────────────

class AsignacionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    usuario_id: UUID
    rol_id: UUID
    contexto_tipo: str
    contexto_id: UUID | None = None
    responsable_id: UUID | None = None
    desde: date
    hasta: date | None = None


class AsignacionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rol_id: UUID | None = None
    contexto_tipo: str | None = None
    contexto_id: UUID | None = None
    responsable_id: UUID | None = None
    desde: date | None = None
    hasta: date | None = None


class AsignacionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

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
