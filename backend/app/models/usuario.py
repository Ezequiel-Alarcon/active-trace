"""`usuario` table — datos personales con PII cifrada en reposo (C-07).

Usuario comparte `id` con AuthUser cuando existe un registro auth asociado.
La FK es lógica, no materializada en DB para permitir usuarios sin cuenta auth.
"""

from __future__ import annotations

from datetime import date as DateType

from sqlalchemy import Boolean, Date, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TenantScopedMixin


class Usuario(Base, TenantScopedMixin):
    __tablename__ = "usuario"

    email_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    email_enc: Mapped[str] = mapped_column(String(2048), nullable=False)
    dni_enc: Mapped[str] = mapped_column(String(2048), nullable=False)
    cuil_enc: Mapped[str] = mapped_column(String(2048), nullable=False)
    cbu_enc: Mapped[str] = mapped_column(String(2048), nullable=False)
    alias_cbu_enc: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    nombre: Mapped[str] = mapped_column(String(128), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(255), nullable=False)
    banco: Mapped[str | None] = mapped_column(String(128), nullable=True)
    regional: Mapped[str | None] = mapped_column(String(128), nullable=True)
    legajo: Mapped[str | None] = mapped_column(String(64), nullable=True)
    legajo_profesional: Mapped[str | None] = mapped_column(String(64), nullable=True)
    fecha_nacimiento: Mapped[DateType | None] = mapped_column(Date, nullable=True)
    genero: Mapped[str | None] = mapped_column(String(16), nullable=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    facturante: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    __table_args__ = (
        Index("ix_usuario_tenant_email_hash", "tenant_id", "email_hash", unique=True),
        Index("ix_usuario_tenant_deleted", "tenant_id", "deleted_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<Usuario id={self.id!r} tenant_id={self.tenant_id!r} "
            f"nombre={self.nombre!r} apellidos={self.apellidos!r}>"
        )
