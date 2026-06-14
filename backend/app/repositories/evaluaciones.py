"""Coloquio repository (C-14 §4).

All queries are tenant-scoped via TenantScopedRepository.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluacion import Evaluacion, ReservaEvaluacion, ResultadoEvaluacion
from app.models.materia import Materia
from app.repositories.base import TenantScopedRepository, get_tenant_repository


class ColoquioRepository:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._repo_evaluacion = TenantScopedRepository(session, Evaluacion, tenant_id)
        self._repo_reserva = TenantScopedRepository(session, ReservaEvaluacion, tenant_id)
        self._repo_resultado = TenantScopedRepository(session, ResultadoEvaluacion, tenant_id)

    async def get_evaluacion(self, evaluacion_id: UUID) -> Evaluacion | None:
        return await self._repo_evaluacion.get_by_id(evaluacion_id)

    async def list_evaluaciones(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        estado: str | None = None,
    ) -> Sequence[Evaluacion]:
        filters = []
        if estado:
            filters.append(Evaluacion.estado == estado)
        return await self._repo_evaluacion.list(
            limit=limit,
            offset=offset,
            order_by=[Evaluacion.created_at.desc()],
            filters=filters if filters else None,
        )

    async def create_evaluacion(self, data: dict[str, Any]) -> Evaluacion:
        return await self._repo_evaluacion.create(data)

    async def update_evaluacion(self, obj: Evaluacion, data: dict[str, Any]) -> Evaluacion:
        return await self._repo_evaluacion.update(obj, data)

    async def count_resultados_by_evaluacion(self, evaluacion_id: UUID) -> int:
        stmt = select(func.count()).select_from(ResultadoEvaluacion).where(
            ResultadoEvaluacion.evaluacion_id == evaluacion_id,
            ResultadoEvaluacion.tenant_id == self._tenant_id,
            ResultadoEvaluacion.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def count_reservas_activas_by_evaluacion(self, evaluacion_id: UUID) -> int:
        stmt = select(func.count()).select_from(ReservaEvaluacion).where(
            ReservaEvaluacion.evaluacion_id == evaluacion_id,
            ReservaEvaluacion.tenant_id == self._tenant_id,
            ReservaEvaluacion.estado == "Activa",
            ReservaEvaluacion.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def count_reservas_activas_by_fecha(
        self, evaluacion_id: UUID, fecha: date
    ) -> int:
        stmt = select(func.count()).select_from(ReservaEvaluacion).where(
            ReservaEvaluacion.evaluacion_id == evaluacion_id,
            ReservaEvaluacion.fecha_reserva == fecha,
            ReservaEvaluacion.tenant_id == self._tenant_id,
            ReservaEvaluacion.estado == "Activa",
            ReservaEvaluacion.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def get_reserva(self, reserva_id: UUID) -> ReservaEvaluacion | None:
        return await self._repo_reserva.get_by_id(reserva_id)

    async def get_reserva_activa(
        self, evaluacion_id: UUID, alumno_id: UUID
    ) -> ReservaEvaluacion | None:
        stmt = (
            select(ReservaEvaluacion)
            .where(
                ReservaEvaluacion.evaluacion_id == evaluacion_id,
                ReservaEvaluacion.alumno_id == alumno_id,
                ReservaEvaluacion.tenant_id == self._tenant_id,
                ReservaEvaluacion.estado == "Activa",
                ReservaEvaluacion.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_reservas_by_evaluacion(
        self, evaluacion_id: UUID, limit: int = 200
    ) -> Sequence[ReservaEvaluacion]:
        stmt = (
            select(ReservaEvaluacion)
            .where(
                ReservaEvaluacion.evaluacion_id == evaluacion_id,
                ReservaEvaluacion.tenant_id == self._tenant_id,
                ReservaEvaluacion.deleted_at.is_(None),
            )
            .order_by(ReservaEvaluacion.fecha_reserva)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_reservas_by_alumno(
        self, alumno_id: UUID, limit: int = 100
    ) -> Sequence[ReservaEvaluacion]:
        stmt = (
            select(ReservaEvaluacion)
            .where(
                ReservaEvaluacion.alumno_id == alumno_id,
                ReservaEvaluacion.tenant_id == self._tenant_id,
                ReservaEvaluacion.deleted_at.is_(None),
            )
            .order_by(ReservaEvaluacion.fecha_reserva.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create_reserva(self, data: dict[str, Any]) -> ReservaEvaluacion:
        return await self._repo_reserva.create(data)

    async def update_reserva(self, obj: ReservaEvaluacion, data: dict[str, Any]) -> ReservaEvaluacion:
        return await self._repo_reserva.update(obj, data)

    async def soft_delete_reserva(self, obj: ReservaEvaluacion) -> None:
        await self._repo_reserva.soft_delete(obj)

    async def list_resultados_by_evaluacion(
        self, evaluacion_id: UUID
    ) -> Sequence[ResultadoEvaluacion]:
        stmt = (
            select(ResultadoEvaluacion)
            .where(
                ResultadoEvaluacion.evaluacion_id == evaluacion_id,
                ResultadoEvaluacion.tenant_id == self._tenant_id,
                ResultadoEvaluacion.deleted_at.is_(None),
            )
            .order_by(ResultadoEvaluacion.created_at)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_resultado(
        self, evaluacion_id: UUID, alumno_id: UUID
    ) -> ResultadoEvaluacion | None:
        stmt = select(ResultadoEvaluacion).where(
            ResultadoEvaluacion.evaluacion_id == evaluacion_id,
            ResultadoEvaluacion.alumno_id == alumno_id,
            ResultadoEvaluacion.tenant_id == self._tenant_id,
            ResultadoEvaluacion.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_resultado(
        self, evaluacion_id: UUID, alumno_id: UUID, nota_final: str
    ) -> ResultadoEvaluacion:
        existing = await self.get_resultado(evaluacion_id, alumno_id)
        if existing:
            return await self._repo_resultado.update(existing, {"nota_final": nota_final})
        return await self._repo_resultado.create({
            "tenant_id": self._tenant_id,
            "evaluacion_id": evaluacion_id,
            "alumno_id": alumno_id,
            "nota_final": nota_final,
        })

    async def materia_exists(self, materia_id: UUID) -> bool:
        repo = get_tenant_repository(Materia, self._session)
        obj = await repo.get_by_id(materia_id)
        return obj is not None

    async def cohorte_exists(self, cohorte_id: UUID) -> bool:
        from app.models.cohorte import Cohorte
        repo = get_tenant_repository(Cohorte, self._session)
        obj = await repo.get_by_id(cohorte_id)
        return obj is not None

    async def alumno_exists(self, alumno_id: UUID) -> bool:
        from app.models.usuario import Usuario
        repo = get_tenant_repository(Usuario, self._session)
        obj = await repo.get_by_id(alumno_id)
        return obj is not None

    async def total_convocados(self) -> int:
        stmt = select(func.count()).select_from(ResultadoEvaluacion).where(
            ResultadoEvaluacion.tenant_id == self._tenant_id,
            ResultadoEvaluacion.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def total_reservas_activas(self) -> int:
        stmt = select(func.count()).select_from(ReservaEvaluacion).where(
            ReservaEvaluacion.tenant_id == self._tenant_id,
            ReservaEvaluacion.estado == "Activa",
            ReservaEvaluacion.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def instancias_activas_count(self) -> int:
        stmt = select(func.count()).select_from(Evaluacion).where(
            Evaluacion.tenant_id == self._tenant_id,
            Evaluacion.estado == "Abierta",
            Evaluacion.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def total_cupos_libres(self) -> int:
        stmt = (
            select(func.sum((Evaluacion.dias_disponibles * Evaluacion.cupos)))
            .select_from(Evaluacion)
            .where(
                Evaluacion.tenant_id == self._tenant_id,
                Evaluacion.estado == "Abierta",
                Evaluacion.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        val = result.scalar_one_or_none()
        return int(val) if val else 0


def get_coloquio_repository(session: AsyncSession, tenant_id: UUID) -> ColoquioRepository:
    return ColoquioRepository(session, tenant_id)