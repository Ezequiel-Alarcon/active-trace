"""Service for derived comisiones."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.comisiones.repository import ComisionesRepository
from app.schemas.comisiones import ComisionRead


class ComisionesService:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._repo = ComisionesRepository(session, tenant_id)

    async def list_active(self) -> list[ComisionRead]:
        rows = await self._repo.list_active()
        return [
            ComisionRead(
                id=f"{row['materia_id']}:{row['cohorte_id']}",
                materia_id=row["materia_id"],
                materia_nombre=row["materia_nombre"],
                cohorte_id=row["cohorte_id"],
                cohorte_nombre=row["cohorte_nombre"],
            )
            for row in rows
        ]
