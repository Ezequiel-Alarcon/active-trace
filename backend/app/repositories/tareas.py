from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tarea import ComentarioTarea, Tarea
from app.repositories.base import TenantScopedRepository


class TareaRepository(TenantScopedRepository[Tarea]):
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        super().__init__(session, Tarea, tenant_id)

    async def list_filtered(
        self,
        *,
        user_id: UUID | None = None,
        estado: str | None = None,
        materia_id: UUID | None = None,
        asignado_a: UUID | None = None,
        q: str | None = None,
        limit: int = 50,
        offset: int = 0,
        order_by: list | None = None,
    ) -> list[Tarea]:
        stmt = (
            select(Tarea)
            .where(Tarea.tenant_id == self._tenant_id)
            .where(Tarea.deleted_at.is_(None))
        )
        stmt = self._apply_filters(stmt, user_id=user_id, estado=estado, materia_id=materia_id, asignado_a=asignado_a, q=q)
        if order_by:
            stmt = stmt.order_by(*order_by)
        else:
            stmt = stmt.order_by(Tarea.created_at.desc())
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_filtered(
        self,
        *,
        user_id: UUID | None = None,
        estado: str | None = None,
        materia_id: UUID | None = None,
        asignado_a: UUID | None = None,
        q: str | None = None,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(Tarea)
            .where(Tarea.tenant_id == self._tenant_id)
            .where(Tarea.deleted_at.is_(None))
        )
        stmt = self._apply_filters(stmt, user_id=user_id, estado=estado, materia_id=materia_id, asignado_a=asignado_a, q=q)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    def _apply_filters(self, stmt, **filters):
        if filters.get("user_id"):
            stmt = stmt.where(Tarea.asignado_a == filters["user_id"])
        if filters.get("estado"):
            from app.models.tarea import EstadoTarea
            stmt = stmt.where(Tarea.estado == EstadoTarea(filters["estado"]))
        if filters.get("materia_id"):
            stmt = stmt.where(Tarea.materia_id == filters["materia_id"])
        if filters.get("asignado_a"):
            stmt = stmt.where(Tarea.asignado_a == filters["asignado_a"])
        if filters.get("q"):
            stmt = stmt.where(Tarea.descripcion.ilike(f"%{filters['q']}%"))
        return stmt


class ComentarioTareaRepository(TenantScopedRepository[ComentarioTarea]):
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        super().__init__(session, ComentarioTarea, tenant_id)

    async def list_by_tarea(
        self,
        tarea_id: UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ComentarioTarea]:
        stmt = (
            select(ComentarioTarea)
            .where(ComentarioTarea.tenant_id == self._tenant_id)
            .where(ComentarioTarea.deleted_at.is_(None))
            .where(ComentarioTarea.tarea_id == tarea_id)
            .order_by(ComentarioTarea.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_tarea(self, tarea_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(ComentarioTarea)
            .where(ComentarioTarea.tenant_id == self._tenant_id)
            .where(ComentarioTarea.deleted_at.is_(None))
            .where(ComentarioTarea.tarea_id == tarea_id)
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one())
