"""`usuario` table — datos personales con PII cifrada en reposo (C-07).

Usuario comparte `id` con AuthUser cuando existe un registro auth asociado.
La FK es lógica, no materializada en DB para permitir usuarios sin cuenta auth.
"""

from __future__ import annotations

import enum
from datetime import date as DateType

from sqlalchemy import Boolean, Date, Enum as SQLEnum, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TenantScopedMixin


class UsuarioEstado(str, enum.Enum):
    activo = "activo"
    inactivo = "inactivo"


class Usuario(Base, TenantScopedMixin):
    __tablename__ = "usuario"

    email_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    email_enc: Mapped[str] = mapped_column(String(2048), nullable=False)
    dni_enc: Mapped[str] = mapped_column(String(2048), nullable=False)
    # TODO: (REVIEW) Auditoría backend/frontend 2026-06-19: la KB
    # `09_decisiones_y_supuestos.md` (S6) describe el CUIL como derivado y de
    # solo lectura, no almacenado de forma independiente. El backend hoy sí lo
    # persiste en `cuil_enc`; resolver la inconsistencia documental o ajustar el
    # modelo/flujo.
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
    estado: Mapped[UsuarioEstado] = mapped_column(
        SQLEnum(UsuarioEstado),
        default=UsuarioEstado.activo,
        server_default=UsuarioEstado.activo.value,
    )
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    # facturante: se mantiene el nombre de columna legacy. KB dice "facturador" pero la BD existente usa "facturante". Se agrega property facturador como alias.
    facturante: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    @property
    def facturador(self) -> bool:
        return self.facturante

    __table_args__ = (
        Index("ix_usuario_tenant_email_hash", "tenant_id", "email_hash", unique=True),
        Index("ix_usuario_tenant_deleted", "tenant_id", "deleted_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<Usuario id={self.id!r} tenant_id={self.tenant_id!r} "
            f"nombre={self.nombre!r} apellidos={self.apellidos!r}>"
        )
