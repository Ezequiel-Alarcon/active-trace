"""`guardia` table — registro de guardias docentes (C-18).

Cada guardia pertenece a un tutor (FK a usuario), una materia y una
cohorte. El scope de visibilidad depende del rol: TUTOR ve solo las
propias, COORDINADOR/ADMIN ven todas.
"""

from __future__ import annotations

from datetime import date, time
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Index, String, Text, Time
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TenantScopedMixin


class Guardia(Base, TenantScopedMixin):
    __tablename__ = "guardia"

    # TODO: (FEAT) Auditoría backend/frontend 2026-06-19: HU-29 / F6.6 piden
    # exponer `estado` de la guardia (mínimo "finalizado") y el modelo no lo
    # persiste. La pantalla de historial no puede mostrar ese dato con el
    # backend actual.

    tutor_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("usuario.id", ondelete="RESTRICT"),
        nullable=False,
    )
    materia_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("materia.id", ondelete="RESTRICT"),
        nullable=False,
    )
    cohorte_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("cohorte.id", ondelete="RESTRICT"),
        nullable=False,
    )
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    hora_inicio: Mapped[time] = mapped_column(Time, nullable=False)
    hora_fin: Mapped[time] = mapped_column(Time, nullable=False)
    titulo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_guardia_tenant_tutor", "tenant_id", "tutor_id"),
        Index("ix_guardia_tenant_materia_cohorte", "tenant_id", "materia_id", "cohorte_id"),
        Index("ix_guardia_tenant_deleted", "tenant_id", "deleted_at"),
    )
