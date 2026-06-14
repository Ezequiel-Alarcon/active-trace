"""AuditLog model (C-05 §2)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditLog(Base):
    """Append-only audit log entry (E-AUD).

    No UPDATE or DELETE path exists for this model. AuditLogRepository
    provides only `create()`. The DB table has no ON DELETE trigger —
    rows are permanent.
    """

    __tablename__ = "audit_log"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    fecha_hora: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    actor_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    impersonado_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    materia_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    accion: Mapped[str] = mapped_column(String(64), nullable=False)
    detalle: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    filas_afectadas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ip: Mapped[str] = mapped_column(String(64), nullable=False)
    user_agent: Mapped[str] = mapped_column(String(512), nullable=False)

    def __repr__(self) -> str:
        return (
            f"AuditLog(id={self.id}, accion={self.accion!r}, "
            f"actor_id={self.actor_id}, impersonado_id={self.impersonado_id})"
        )