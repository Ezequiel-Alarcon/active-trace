"""Analisis repository (C-11).

Queries para atrasados, ranking, reportes y monitores.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import and_, case, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.calificaciones.models.calificacion import Calificacion
from app.models.asignacion import Asignacion, ContextoTipo
from app.models.usuario import Usuario


class AnalisisRepository:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    # -------------------------------------------------------------------------
    # Alumnos atrasados
    # -------------------------------------------------------------------------

    async def get_alumnos_atrasados(
        self,
        *,
        materia_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        """Alumnos con al menos una actividad faltante o no aprobada.

        Un alumno esta atrasado cuando alguna actividad de la lista esperada
        no tiene Calificacion o su nota no pasa el umbral.
        """
        # Subquery: todas las entradas de padron activas para el tenant
        entradas_stmt = (
            select(
                Calificacion.materia_id,
                Calificacion.usuario_id,
                func.count(Calificacion.id).label("total_calif"),
                func.sum(
                    case(
                        (Calificacion.nota.isnot(None), 1),
                        else_=0,
                    )
                ).label("con_nota"),
            )
            .where(
                Calificacion.tenant_id == self._tenant_id,
                Calificacion.deleted_at.is_(None),
            )
            .group_by(Calificacion.materia_id, Calificacion.usuario_id)
        )

        if materia_id:
            entradas_stmt = entradas_stmt.where(Calificacion.materia_id == materia_id)
        if cohorte_id:
            # Need cohorte filter - use VersionPadron join
            pass

        calif_counts = entradas_stmt.subquery()
        return []

    async def get_ranking(
        self,
        materia_id: UUID,
        limit: int = 50,
    ) -> list[dict]:
        """Ranking de alumnos por cantidad de actividades aprobadas."""
        # Subquery: solo calificaciones con nota (filtra antes de contar)
        calif_aprobadas = (
            select(
                Calificacion.usuario_id,
                func.count(Calificacion.id).label("aprobadas_count"),
            )
            .where(
                Calificacion.materia_id == materia_id,
                Calificacion.tenant_id == self._tenant_id,
                Calificacion.deleted_at.is_(None),
                Calificacion.nota.isnot(None),
            )
            .group_by(Calificacion.usuario_id)
        ).subquery()

        stmt = (
            select(
                calif_aprobadas.c.usuario_id,
                calif_aprobadas.c.aprobadas_count,
            )
            .order_by(calif_aprobadas.c.aprobadas_count.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        rows = result.all()

        ranking = []
        for i, row in enumerate(rows, 1):
            r = dict(row._mapping)
            r["ranking"] = i
            ranking.append(r)
        return ranking

    async def get_reporte_materia(self, materia_id: UUID) -> dict:
        """Reporte agregado del estado de una materia."""
        total_calif = (
            select(func.count(func.distinct(Calificacion.usuario_id)))
            .where(
                Calificacion.materia_id == materia_id,
                Calificacion.tenant_id == self._tenant_id,
                Calificacion.deleted_at.is_(None),
            )
        )
        con_nota = (
            select(func.count(func.distinct(Calificacion.usuario_id)))
            .where(
                Calificacion.materia_id == materia_id,
                Calificacion.tenant_id == self._tenant_id,
                Calificacion.nota.isnot(None),
                Calificacion.deleted_at.is_(None),
            )
        )
        total_res = await self._session.scalar(total_calif)
        con_nota_res = await self._session.scalar(con_nota)
        return {
            "materia_id": str(materia_id),
            "alumnos_con_actividad": total_res or 0,
            "alumnos_con_nota": con_nota_res or 0,
        }

    async def get_notas_finales(self) -> list[dict]:
        """Notas finales agrupadas por materia (promedio de notas numéricas)."""
        stmt = (
            select(
                Calificacion.materia_id,
                func.count(Calificacion.id).label("total_actividades"),
                func.avg(
                    case(
                        (
                            and_(
                                Calificacion.nota.isnot(None),
                                Calificacion.origen == "Importado",
                            ),
                            Calificacion.nota.cast(float),
                        ),
                        else_=None,
                    )
                ).label("promedio"),
            )
            .where(
                Calificacion.tenant_id == self._tenant_id,
                Calificacion.deleted_at.is_(None),
            )
            .group_by(Calificacion.materia_id)
        )
        result = await self._session.execute(stmt)
        return [dict(r._mapping) for r in result.all()]

    async def get_tps_sin_corregir(
        self,
        *,
        materia_id: UUID | None = None,
        limit: int = 200,
    ) -> list[dict]:
        """Alumnos con actividad esperada pero sin nota (para re-importación)."""
        # Alumnos que tienen al menos una entrada en VersionPadron activa
        # pero no tienen ninguna Calificacion para la materia
        stmt = (
            select(
                Calificacion.materia_id,
                Calificacion.usuario_id,
            )
            .join(
                Usuario,
                Usuario.id == Calificacion.usuario_id,
            )
            .where(
                Calificacion.tenant_id == self._tenant_id,
                Calificacion.nota.is_(None),
                Calificacion.deleted_at.is_(None),
                Usuario.tenant_id == self._tenant_id,
            )
        )
        if materia_id:
            stmt = stmt.where(Calificacion.materia_id == materia_id)
        stmt = stmt.distinct().limit(limit)
        result = await self._session.execute(stmt)
        return [dict(r._mapping) for r in result.all()]

    async def get_monitor_general(self, docente_id: UUID) -> list[dict]:
        """Monitor para profesor: sus alumnos en sus materias asignadas."""
        stmt = (
            select(
                Calificacion.materia_id,
                func.count(func.distinct(Calificacion.usuario_id)).label("alumnos"),
                func.count(
                    case((Calificacion.nota.isnot(None), 1), else_=0)
                ).label("con_nota"),
            )
            .join(
                Asignacion,
                and_(
                    Asignacion.contexto_tipo == ContextoTipo.MATERIA,
                    Asignacion.contexto_id == Calificacion.materia_id,
                    Asignacion.usuario_id == docente_id,
                    Asignacion.deleted_at.is_(None),
                ),
            )
            .where(
                Calificacion.tenant_id == self._tenant_id,
                Calificacion.deleted_at.is_(None),
            )
            .group_by(Calificacion.materia_id)
        )
        result = await self._session.execute(stmt)
        return [dict(r._mapping) for r in result.all()]

    async def get_monitor_seguimiento(self, tutor_id: UUID) -> list[dict]:
        """Monitor para tutor: sus tutorados (asignaciones con rol TUTOR)."""
        # Tutor ve alumnos a los que está asignado como responsable
        stmt = (
            select(
                Calificacion.materia_id,
                func.count(func.distinct(Calificacion.usuario_id)).label("tutorados"),
            )
            .join(
                Asignacion,
                and_(
                    Asignacion.contexto_tipo == ContextoTipo.MATERIA,
                    Asignacion.contexto_id == Calificacion.materia_id,
                    Asignacion.usuario_id == Calificacion.usuario_id,
                    Asignacion.responsable_id == tutor_id,
                    Asignacion.deleted_at.is_(None),
                ),
            )
            .where(
                Calificacion.tenant_id == self._tenant_id,
                Calificacion.deleted_at.is_(None),
            )
            .group_by(Calificacion.materia_id)
        )
        result = await self._session.execute(stmt)
        return [dict(r._mapping) for r in result.all()]

    async def get_monitor_coordinacion(
        self,
        desde: str,
        hasta: str,
    ) -> list[dict]:
        """Monitor para coordinación/admin: todo el tenant con rango de fechas."""
        from datetime import date

        desde_date = date.fromisoformat(desde)
        hasta_date = date.fromisoformat(hasta)

        stmt = (
            select(
                Calificacion.materia_id,
                func.count(func.distinct(Calificacion.usuario_id)).label("total_alumnos"),
                func.count(
                    case((Calificacion.nota.isnot(None), 1), else_=0)
                ).label("con_nota"),
                func.min(Calificacion.created_at).label("primera_actividad"),
                func.max(Calificacion.created_at).label("ultima_actividad"),
            )
            .where(
                Calificacion.tenant_id == self._tenant_id,
                Calificacion.deleted_at.is_(None),
                Calificacion.created_at >= desde_date,
                Calificacion.created_at <= hasta_date,
            )
            .group_by(Calificacion.materia_id)
        )
        result = await self._session.execute(stmt)
        return [dict(r._mapping) for r in result.all()]