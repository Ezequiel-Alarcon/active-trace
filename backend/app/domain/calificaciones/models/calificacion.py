"""Calificacion model (C-10).

Representa una calificacion de un estudiante en una materia/asignacion.
El campo `nota` es JSONB (null | number | string | list) y `aprobado`
se deriva en el servicio, nunca se almacena.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import JSON, Index, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TenantScopedMixin


class Calificacion(Base, TenantScopedMixin):
    __tablename__ = "calificacion"

    materia_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    usuario_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    asignacion_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    version_padron_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        nullable=True,
    )
    nota: Mapped[dict | list | float | int | str | None] = mapped_column(JSON, nullable=True)
    origen: Mapped[str] = mapped_column(String(16), nullable=False)
    import_batch_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    created_by: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)

    __table_args__ = (
        Index("ix_calificacion_tenant", "tenant_id"),
        Index("ix_calificacion_materia", "materia_id"),
        Index("ix_calificacion_usuario", "usuario_id"),
        Index("ix_calificacion_asignacion", "asignacion_id"),
        Index("ix_calificacion_tenant_deleted", "tenant_id", "deleted_at"),
        Index("ix_calificacion_import_batch", "import_batch_id"),
        Index(
            "ix_calificacion_materia_usuario_asignacion_deleted",
            "materia_id",
            "usuario_id",
            "asignacion_id",
            "deleted_at",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Calificacion id={self.id!r} materia_id={self.materia_id!r} "
            f"usuario_id={self.usuario_id!r} origen={self.origen!r}>"
        )