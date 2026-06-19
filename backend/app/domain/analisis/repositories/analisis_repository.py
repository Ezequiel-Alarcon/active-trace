"""Analisis repository (C-11).

Queries para atrasados, ranking, reportes y monitores.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.calificaciones.models.calificacion import Calificacion
from app.domain.calificaciones.models.umbral_materia import UmbralMateria
from app.models.asignacion import Asignacion, ContextoTipo
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.padron import EntradaPadron, VersionPadron
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
        """Load active-roster rows and related grades for delayed-student analysis."""
        stmt = (
            select(
                EntradaPadron,
                VersionPadron.materia_id,
                VersionPadron.cohorte_id,
                VersionPadron.actividades,
                Materia.nombre.label("materia_nombre"),
                Cohorte.nombre.label("cohorte_nombre"),
                UmbralMateria.umbral_pct,
                UmbralMateria.conjunto_aprobado,
            )
            .join(
                VersionPadron,
                (VersionPadron.id == EntradaPadron.version_id)
                & (VersionPadron.tenant_id == self._tenant_id)
                & (VersionPadron.activa.is_(True))
                & (VersionPadron.deleted_at.is_(None)),
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
            .outerjoin(
                UmbralMateria,
                (UmbralMateria.materia_id == VersionPadron.materia_id)
                & (UmbralMateria.tenant_id == self._tenant_id)
                & (UmbralMateria.asignacion_id.is_(None))
                & (UmbralMateria.deleted_at.is_(None)),
            )
            .where(
                EntradaPadron.tenant_id == self._tenant_id,
                EntradaPadron.deleted_at.is_(None),
            )
            .order_by(EntradaPadron.apellidos, EntradaPadron.nombre)
        )
        if materia_id:
            stmt = stmt.where(VersionPadron.materia_id == materia_id)
        if cohorte_id:
            stmt = stmt.where(VersionPadron.cohorte_id == cohorte_id)

        result = await self._session.execute(stmt.offset(offset).limit(limit))
        rows = [dict(row._mapping) for row in result.all()]
        for row in rows:
            usuario_id = row["EntradaPadron"].usuario_id
            calif_stmt = select(Calificacion).where(
                Calificacion.tenant_id == self._tenant_id,
                Calificacion.materia_id == row["materia_id"],
                Calificacion.deleted_at.is_(None),
            )
            if usuario_id is None:
                calificaciones = []
            else:
                calif_result = await self._session.execute(calif_stmt.where(Calificacion.usuario_id == usuario_id))
                calificaciones = list(calif_result.scalars().all())
            row["calificaciones"] = calificaciones
        return rows

    async def get_ranking(
        self,
        materia_id: UUID,
        limit: int = 50,
    ) -> list[dict]:
        stmt = (
            select(Calificacion.usuario_id, func.count(Calificacion.id).label("aprobadas_count"))
            .where(
                Calificacion.materia_id == materia_id,
                Calificacion.tenant_id == self._tenant_id,
                Calificacion.deleted_at.is_(None),
                Calificacion.nota.isnot(None),
            )
            .group_by(Calificacion.usuario_id)
            .order_by(func.count(Calificacion.id).desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [dict(row._mapping) for row in result.all()]

    async def get_ranking_rows(self, materia_id: UUID) -> list[dict]:
        stmt = (
            select(
                Calificacion,
                Usuario.nombre,
                Usuario.apellidos,
                Usuario.email_enc,
                Materia.nombre.label("materia_nombre"),
                UmbralMateria.umbral_pct,
                UmbralMateria.conjunto_aprobado,
            )
            .outerjoin(
                Usuario,
                (Usuario.id == Calificacion.usuario_id)
                & (Usuario.tenant_id == self._tenant_id)
                & (Usuario.deleted_at.is_(None)),
            )
            .join(
                Materia,
                (Materia.id == Calificacion.materia_id)
                & (Materia.tenant_id == self._tenant_id)
                & (Materia.deleted_at.is_(None)),
            )
            .outerjoin(
                UmbralMateria,
                (UmbralMateria.materia_id == Calificacion.materia_id)
                & (UmbralMateria.tenant_id == self._tenant_id)
                & (UmbralMateria.asignacion_id.is_(None))
                & (UmbralMateria.deleted_at.is_(None)),
            )
            .where(
                Calificacion.materia_id == materia_id,
                Calificacion.tenant_id == self._tenant_id,
                Calificacion.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        rows = [dict(row._mapping) for row in result.all()]
        return rows

    async def get_reporte_materia(self, materia_id: UUID) -> dict:
        """Reporte agregado del estado de una materia."""
        rows = await self.get_alumnos_atrasados(materia_id=materia_id, limit=10000)
        total_calif = await self._session.scalar(
            select(func.count(func.distinct(Calificacion.usuario_id))).where(
                Calificacion.materia_id == materia_id,
                Calificacion.tenant_id == self._tenant_id,
                Calificacion.deleted_at.is_(None),
            )
        )
        con_nota = await self._session.scalar(
            select(func.count(func.distinct(Calificacion.usuario_id))).where(
                Calificacion.materia_id == materia_id,
                Calificacion.tenant_id == self._tenant_id,
                Calificacion.nota.isnot(None),
                Calificacion.deleted_at.is_(None),
            )
        )
        return {
            "materia_id": str(materia_id),
            "alumnos_con_actividad": total_calif or len(rows),
            "alumnos_con_nota": con_nota or sum(1 for row in rows if row["calificaciones"]),
            "rows": rows,
        }

    async def get_notas_finales(self) -> list[dict]:
        """Load rows for final-grade aggregation by materia."""
        stmt = (
            select(
                Calificacion,
                Materia.nombre.label("materia_nombre"),
                UmbralMateria.umbral_pct,
                UmbralMateria.conjunto_aprobado,
            )
            .join(
                Materia,
                (Materia.id == Calificacion.materia_id)
                & (Materia.tenant_id == self._tenant_id)
                & (Materia.deleted_at.is_(None)),
            )
            .outerjoin(
                UmbralMateria,
                (UmbralMateria.materia_id == Calificacion.materia_id)
                & (UmbralMateria.tenant_id == self._tenant_id)
                & (UmbralMateria.asignacion_id.is_(None))
                & (UmbralMateria.deleted_at.is_(None)),
            )
            .where(
                Calificacion.tenant_id == self._tenant_id,
                Calificacion.deleted_at.is_(None),
            )
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
