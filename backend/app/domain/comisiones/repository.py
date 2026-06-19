"""Tenant-scoped repository for derived comisiones."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.padron import VersionPadron


class ComisionesRepository:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def list_active(self) -> list[dict]:
        stmt = (
            select(
                VersionPadron.materia_id,
                Materia.nombre.label("materia_nombre"),
                VersionPadron.cohorte_id,
                Cohorte.nombre.label("cohorte_nombre"),
            )
            .join(
                Materia,
                (Materia.id == VersionPadron.materia_id)
                & (Materia.tenant_id == self._tenant_id)
                & (Materia.deleted_at.is_(None)),
            )
            .join(
                Cohorte,
                (Cohorte.id == VersionPadron.cohorte_id)
                & (Cohorte.tenant_id == self._tenant_id)
                & (Cohorte.deleted_at.is_(None)),
            )
            .where(
                VersionPadron.tenant_id == self._tenant_id,
                VersionPadron.activa.is_(True),
                VersionPadron.deleted_at.is_(None),
            )
            .distinct()
            .order_by(Materia.nombre, Cohorte.nombre)
        )
        result = await self._session.execute(stmt)
        return [dict(row._mapping) for row in result.all()]
