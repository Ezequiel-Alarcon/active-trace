"""RBAC Pydantic schemas (C-04 §7).

Request/response DTOs for the admin catalog API.
All schemas use extra='forbid' per project convention.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PermisoSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    modulo: str
    accion: str
    created_at: datetime
    updated_at: datetime


class RolCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str
    descripcion: str | None = None


class RolUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str | None = None
    descripcion: str | None = None


class RolSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    nombre: str
    descripcion: str | None
    created_at: datetime
    updated_at: datetime


class RolDetail(RolSummary):
    model_config = ConfigDict(extra="forbid")

    permisos: list[PermisoSummary] = []


class PermisoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    modulo: str
    accion: str


class RolPermisoAttach(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pass


class PermissionsMeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    permissions: list[str]
