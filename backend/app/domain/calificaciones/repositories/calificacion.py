"""Calificacion repository (C-10).

Extends TenantScopedRepository con batch insert y queries filtradas.
"""

from __future__ import annotations

from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.calificaciones.models.calificacion import Calificacion
from app.repositories.base import TenantScopedRepository


class CalificacionRepository(TenantScopedRepository[Calificacion]):
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        super().__init__(session, Calificacion, tenant_id)

    async def create_many(
        self,
        rows_data: list[dict[str, Any]],
        import_batch_id: UUID,
        created_by: UUID,
    ) -> list[Calificacion]:
        """Batch insert de calificaciones."""
        objects: list[Calificacion] = []
        for row in rows_data:
            obj = Calificacion(
                tenant_id=self._tenant_id,
                materia_id=row["materia_id"],
                usuario_id=row["usuario_id"],
                asignacion_id=row.get("asignacion_id"),
                version_padron_id=row.get("version_padron_id"),
                nota=row.get("nota"),
                origen=row.get("origen", "Importado"),
                import_batch_id=import_batch_id,
                created_by=created_by,
            )
            self._session.add(obj)
            objects.append(obj)
        await self._session.flush()
        return objects

    async def get_filtered(
        self,
        *,
        materia_id: UUID | None = None,
        usuario_id: UUID | None = None,
        asignacion_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[Calificacion]:
        filters = []
        if materia_id is not None:
            filters.append(Calificacion.materia_id == materia_id)
        if usuario_id is not None:
            filters.append(Calificacion.usuario_id == usuario_id)
        if asignacion_id is not None:
            filters.append(Calificacion.asignacion_id == asignacion_id)
        return await self.list(limit=limit, offset=offset, filters=filters)

    async def get_by_materia_usuario_asignacion(
        self,
        materia_id: UUID,
        usuario_id: UUID,
        asignacion_id: UUID | None,
    ) -> Calificacion | None:
        stmt = (
            select(Calificacion)
            .where(Calificacion.tenant_id == self._tenant_id)
            .where(Calificacion.materia_id == materia_id)
            .where(Calificacion.usuario_id == usuario_id)
            .where(Calificacion.asignacion_id == asignacion_id)
            .where(Calificacion.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def exists_for_materia_usuario_asignacion(
        self,
        materia_id: UUID,
        usuario_id: UUID,
        asignacion_id: UUID | None,
    ) -> bool:
        stmt = (
            select(Calificacion.id)
            .where(Calificacion.tenant_id == self._tenant_id)
            .where(Calificacion.materia_id == materia_id)
            .where(Calificacion.usuario_id == usuario_id)
            .where(Calificacion.asignacion_id == asignacion_id)
            .where(Calificacion.deleted_at.is_(None))
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None