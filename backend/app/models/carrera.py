"""`carrera` table — catálogo de carreras académicas por tenant (C-06).

Cada carrera pertenece a un tenant. La unicidad es compuesta por
(tenant_id, codigo). El estado (Activa/Inactiva) controla si se
pueden crear cohortes hijas.
"""

from __future__ import annotations

import enum

from sqlalchemy import Enum, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TenantScopedMixin


class CarreraEstado(str, enum.Enum):
    ACTIVA = "Activa"
    INACTIVA = "Inactiva"


class Carrera(Base, TenantScopedMixin):
    __tablename__ = "carrera"

    codigo: Mapped[str] = mapped_column(String(64), nullable=False)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    estado: Mapped[CarreraEstado] = mapped_column(
        Enum(CarreraEstado, name="carrera_estado", values_callable=lambda x: [m.value for m in x]),
        nullable=False,
        default=CarreraEstado.ACTIVA,
    )

    __table_args__ = (
        Index("ix_carrera_tenant_codigo", "tenant_id", "codigo", unique=True),
        Index("ix_carrera_tenant_deleted", "tenant_id", "deleted_at"),
    )
