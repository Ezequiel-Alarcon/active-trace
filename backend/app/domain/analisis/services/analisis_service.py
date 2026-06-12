"""Analisis service (C-11).

Servicios para consultas de atrasados, ranking, reportes y monitores.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.analisis.repositories.analisis_repository import AnalisisRepository


class AnalisisServiceError(Exception):
    pass


class FechaInvalidaError(AnalisisServiceError):
    pass


class RangoExcedidoError(AnalisisServiceError):
    pass


class AnalisisService:
    _MAX_DIAS_RANGO = 365

    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._repo = AnalisisRepository(session, tenant_id)

    async def get_ranking(self, materia_id: UUID, limit: int = 50) -> list[dict]:
        """Ranking de alumnos por cantidad de actividades aprobadas."""
        return await self._repo.get_ranking(materia_id, limit)

    async def get_reporte_materia(self, materia_id: UUID) -> dict:
        """Reporte agregado del estado de una materia."""
        return await self._repo.get_reporte_materia(materia_id)

    async def get_notas_finales(self) -> list[dict]:
        """Notas finales agrupadas por materia."""
        return await self._repo.get_notas_finales()

    async def get_tps_sin_corregir(
        self,
        *,
        materia_id: UUID | None = None,
        limit: int = 200,
    ) -> list[dict]:
        """Alumnos con actividad esperada pero sin nota."""
        return await self._repo.get_tps_sin_corregir(
            materia_id=materia_id,
            limit=limit,
        )

    async def get_monitor_general(self, docente_id: UUID) -> list[dict]:
        """Monitor para profesor: sus alumnos en sus materias."""
        return await self._repo.get_monitor_general(docente_id)

    async def get_monitor_seguimiento(self, tutor_id: UUID) -> list[dict]:
        """Monitor para tutor: sus tutorados."""
        return await self._repo.get_monitor_seguimiento(tutor_id)

    async def get_monitor_coordinacion(
        self,
        desde: str,
        hasta: str,
    ) -> list[dict]:
        """Monitor para coordinación/admin con rango de fechas."""
        desde_date = date.fromisoformat(desde)
        hasta_date = date.fromisoformat(hasta)
        dias = (hasta_date - desde_date).days
        if dias < 0:
            raise FechaInvalidaError("'desde' debe ser anterior a 'hasta'")
        if dias > self._MAX_DIAS_RANGO:
            raise RangoExcedidoError(
                f"El rango no puede superar {self._MAX_DIAS_RANGO} días"
            )
        return await self._repo.get_monitor_coordinacion(desde, hasta)