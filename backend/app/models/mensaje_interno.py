from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TenantScopedMixin


class MensajeInterno(Base, TenantScopedMixin):
    __tablename__ = "mensaje_interno"

    asunto: Mapped[str] = mapped_column(Text, nullable=False)
    cuerpo: Mapped[str] = mapped_column(Text, nullable=False)
    remitente_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("usuario.id", ondelete="RESTRICT"),
        nullable=False,
    )
    destinatario_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("usuario.id", ondelete="RESTRICT"),
        nullable=False,
    )
    hilo_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    padre_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("mensaje_interno.id", ondelete="SET NULL"),
        nullable=True,
    )
    leido_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    __table_args__ = (
        Index("ix_mensaje_interno_tenant", "tenant_id"),
        Index("ix_mensaje_interno_tenant_deleted", "tenant_id", "deleted_at"),
        Index("ix_mensaje_interno_remitente", "tenant_id", "remitente_id"),
        Index("ix_mensaje_interno_destinatario", "tenant_id", "destinatario_id"),
        Index("ix_mensaje_interno_hilo", "tenant_id", "hilo_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<MensajeInterno id={self.id!r} tenant_id={self.tenant_id!r} "
            f"asunto={self.asunto!r}>"
        )
