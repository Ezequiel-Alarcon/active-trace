"""`asignacion` table — vinculo Usuario <-> Rol con contexto y vigencia (C-07).

Cada asignacion asocia un usuario a un rol dentro de un contexto academico
(Global, Carrera, Cohorte, Materia) con fechas desde/hasta.
"""

from __future__ import annotations

import enum
from datetime import date as DateType
from uuid import UUID

from sqlalchemy import Date, Enum, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TenantScopedMixin


class ContextoTipo(str, enum.Enum):
    GLOBAL = "Global"
    CARRERA = "Carrera"
    COHORTE = "Cohorte"
    MATERIA = "Materia"


class Asignacion(Base, TenantScopedMixin):
    __tablename__ = "asignacion"

    usuario_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        nullable=False,
    )
    rol_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        nullable=False,
    )
    contexto_tipo: Mapped[ContextoTipo] = mapped_column(
        Enum(ContextoTipo, name="contexto_tipo", values_callable=lambda x: [m.value for m in x]),
        nullable=False,
    )
    contexto_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        nullable=True,
    )
    materia_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    cohorte_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    comisiones: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    responsable_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        nullable=True,
    )
    desde: Mapped[DateType] = mapped_column(Date, nullable=False)
    hasta: Mapped[DateType | None] = mapped_column(Date, nullable=True)

    __table_args__ = (
        Index("ix_asignacion_tenant_usuario", "tenant_id", "usuario_id"),
        Index("ix_asignacion_tenant_rol", "tenant_id", "rol_id"),
        Index("ix_asignacion_tenant_materia", "tenant_id", "materia_id"),
        Index("ix_asignacion_tenant_cohorte", "tenant_id", "cohorte_id"),
        Index("ix_asignacion_tenant_contexto", "tenant_id", "contexto_tipo", "contexto_id"),
        Index("ix_asignacion_tenant_deleted", "tenant_id", "deleted_at"),
    )

    @property
    def estado_vigencia(self) -> str:
        today = DateType.today()
        if self.desde <= today and (self.hasta is None or self.hasta >= today):
            return "Vigente"
        return "Vencida"

    def __repr__(self) -> str:
        return (
            f"<Asignacion id={self.id!r} tenant_id={self.tenant_id!r} "
            f"usuario_id={self.usuario_id!r} rol_id={self.rol_id!r} "
            f"contexto_tipo={self.contexto_tipo.value!r}>"
        )
