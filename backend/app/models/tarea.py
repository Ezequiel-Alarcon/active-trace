from __future__ import annotations

import enum
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TenantScopedMixin


class EstadoTarea(str, enum.Enum):
    PENDIENTE = "Pendiente"
    EN_PROGRESO = "En progreso"
    RESUELTA = "Resuelta"
    CANCELADA = "Cancelada"


class Tarea(Base, TenantScopedMixin):
    __tablename__ = "tarea"

    materia_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    asignado_a: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    asignado_por: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    estado: Mapped[EstadoTarea] = mapped_column(
        Enum(EstadoTarea, name="estado_tarea", values_callable=lambda x: [m.value for m in x]),
        nullable=False,
        default=EstadoTarea.PENDIENTE,
    )
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    contexto_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)

    __table_args__ = (
        Index("ix_tarea_tenant", "tenant_id"),
        Index("ix_tarea_tenant_deleted", "tenant_id", "deleted_at"),
        Index("ix_tarea_asignado_a", "tenant_id", "asignado_a"),
        Index("ix_tarea_estado", "tenant_id", "estado"),
    )


class ComentarioTarea(Base, TenantScopedMixin):
    __tablename__ = "comentario_tarea"

    tarea_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("tarea.id", ondelete="CASCADE"), nullable=False)
    autor_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    texto: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index("ix_comentario_tarea_tenant", "tenant_id"),
        Index("ix_comentario_tarea_tenant_deleted", "tenant_id", "deleted_at"),
        Index("ix_comentario_tarea_tarea", "tenant_id", "tarea_id"),
    )
