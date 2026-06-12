"""UmbralMateria repository (C-10).

Extends TenantScopedRepository con get_by_materia_asignacion y fallback.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.calificaciones.models.umbral_materia import UmbralMateria
from app.repositories.base import TenantScopedRepository


_DEFAULT_UMBRAL_PCT = 60
_DEFAULT_CONJUNTO = ["A", "B+", "C", "7", "8", "9", "10"]


class UmbralMateriaRepository(TenantScopedRepository[UmbralMateria]):
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        super().__init__(session, UmbralMateria, tenant_id)

    async def get_by_materia_asignacion(
        self,
        materia_id: UUID,
        asignacion_id: UUID | None,
    ) -> UmbralMateria | None:
        """Get umbral for specific materia+asignacion, or fallback to course-level default."""
        if asignacion_id is not None:
            stmt = (
                select(UmbralMateria)
                .where(UmbralMateria.tenant_id == self._tenant_id)
                .where(UmbralMateria.materia_id == materia_id)
                .where(UmbralMateria.asignacion_id == asignacion_id)
                .where(UmbralMateria.deleted_at.is_(None))
            )
            result = await self._session.execute(stmt)
            umbral = result.scalar_one_or_none()
            if umbral is not None:
                return umbral

        stmt = (
            select(UmbralMateria)
            .where(UmbralMateria.tenant_id == self._tenant_id)
            .where(UmbralMateria.materia_id == materia_id)
            .where(UmbralMateria.asignacion_id.is_(None))
            .where(UmbralMateria.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_default_for_materia(self, materia_id: UUID) -> dict:
        """Return default umbral dict when no UmbralMateria exists for materia."""
        return {
            "umbral_pct": _DEFAULT_UMBRAL_PCT,
            "conjunto_aprobado": _DEFAULT_CONJUNTO,
        }

    async def create(self, data: dict) -> UmbralMateria:
        if isinstance(data, dict):
            data = {**data, "tenant_id": self._tenant_id}
        return await super().create(data)

    async def update(self, obj: UmbralMateria, data: dict) -> UmbralMateria:
        return await super().update(obj, data)