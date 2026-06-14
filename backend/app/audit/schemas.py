"""Pydantic schemas for audit log (C-05 §7)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AuditLogCreate(BaseModel):
    """Internal schema used by the repository."""

    model_config = ConfigDict(extra="forbid")

    actor_id: UUID
    accion: str
    impersonado_id: UUID | None = None
    materia_id: UUID | None = None
    detalle: dict[str, Any] | None = None
    filas_afectadas: int = 0
    ip: str = "0.0.0.0"
    user_agent: str = "unknown"


class AuditLogResponse(BaseModel):
    """Public audit log entry response."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    fecha_hora: datetime
    actor_id: UUID
    impersonado_id: UUID | None
    materia_id: UUID | None
    accion: str
    detalle: dict[str, Any] | None
    filas_afectadas: int
    ip: str
    user_agent: str


class AuditLogFilter(BaseModel):
    """Filter parameters for audit log queries."""

    model_config = ConfigDict(extra="forbid")

    actor_id: UUID | None = None
    accion: str | None = None
    from_date: datetime | None = None
    to_date: datetime | None = None
    impersonado_id: UUID | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
    all_tenants: bool = False


class AuditLogPageResponse(BaseModel):
    """Paginated audit log response."""

    model_config = ConfigDict(extra="forbid")

    total: int
    page: int
    page_size: int
    items: list[AuditLogResponse]


# ── C-19: Panel de Auditoría — Métricas ──────────────────────────────────────


class ActionsPerDayResponse(BaseModel):
    """Actions grouped by day."""

    model_config = ConfigDict(extra="forbid")

    date: datetime
    count: int


class ComunicacionStatusItem(BaseModel):
    """Communication status counts by materia and docente."""

    model_config = ConfigDict(extra="forbid")

    materia_id: UUID | None
    docente_id: UUID
    pending: int
    sending: int
    ok: int
    failed: int
    cancelled: int


class InteractionItem(BaseModel):
    """Interaction counts by materia, docente, and action."""

    model_config = ConfigDict(extra="forbid")

    materia_id: UUID | None
    docente_id: UUID
    accion: str
    count: int