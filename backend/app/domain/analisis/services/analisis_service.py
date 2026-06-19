"""Analisis service (C-11).

Servicios para consultas de atrasados, ranking, reportes y monitores.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.analisis.repositories.analisis_repository import AnalisisRepository
from app.domain.calificaciones.models.calificacion import Calificacion
from app.domain.calificaciones.services.aprobado import derivar_aprobado
from app.core.security.crypto import decrypt
from app.repositories.padron import decrypt_entrada_email


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
        rows = await self._repo.get_ranking_rows(materia_id)
        grouped: dict[UUID, dict] = {}
        for row in rows:
            calificacion: Calificacion = row["Calificacion"]
            item = grouped.setdefault(
                calificacion.usuario_id,
                {
                    "usuario_id": calificacion.usuario_id,
                    "nombre": f"{row['nombre'] or ''} {row['apellidos'] or ''}".strip(),
                    "email": decrypt(row["email_enc"], tenant_id=self._tenant_id, aad_suffix="usuario.email") if row["email_enc"] else "",
                    "materia_nombre": row["materia_nombre"],
                    "cantidad_aprobadas": 0,
                    "cantidad_totales": 0,
                    "notas_numericas": [],
                },
            )
            umbral_pct = row["umbral_pct"] or 60
            conjunto = row["conjunto_aprobado"] or ["Satisfactorio", "Supera lo esperado"]
            if calificacion.nota is not None:
                item["cantidad_totales"] += 1
                if isinstance(calificacion.nota, int | float):
                    item["notas_numericas"].append(float(calificacion.nota))
                if derivar_aprobado(calificacion.nota, umbral_pct, conjunto):
                    item["cantidad_aprobadas"] += 1

        ranked = [item for item in grouped.values() if item["cantidad_aprobadas"] > 0]
        ranked.sort(key=lambda item: item["cantidad_aprobadas"], reverse=True)
        result = []
        for posicion, item in enumerate(ranked[:limit], 1):
            notas = item.pop("notas_numericas")
            item["posicion"] = posicion
            item["nota_promedio"] = sum(notas) / len(notas) if notas else None
            result.append(item)
        return result

    async def get_alumnos_atrasados(
        self,
        *,
        materia_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        rows = await self._repo.get_alumnos_atrasados(
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            limit=limit,
            offset=offset,
        )
        alumnos = []
        for row in rows:
            entrada = row["EntradaPadron"]
            actividades = row["actividades"] or []
            calificaciones = row["calificaciones"]
            umbral_pct = row["umbral_pct"] or 60
            conjunto = row["conjunto_aprobado"] or ["Satisfactorio", "Supera lo esperado"]
            failing = [c for c in calificaciones if c.nota is not None and not derivar_aprobado(c.nota, umbral_pct, conjunto)]
            missing = len(actividades) > len([c for c in calificaciones if c.nota is not None])
            if not failing and not missing:
                continue
            nota_actual = failing[0].nota if failing else None
            alumnos.append(
                {
                    "usuario_id": entrada.usuario_id,
                    "email": decrypt_entrada_email(entrada),
                    "nombre": f"{entrada.nombre} {entrada.apellidos}",
                    "materia_id": row["materia_id"],
                    "materia_nombre": row["materia_nombre"],
                    "asignacion_id": failing[0].asignacion_id if failing else None,
                    "asignacion_nombre": None,
                    "estado": "atrasado",
                    "nota_actual": nota_actual,
                    "umbral_pct": umbral_pct,
                }
            )
        return {"total": len(alumnos), "limit": limit, "offset": offset, "alumnos": alumnos}

    async def get_reporte_materia(self, materia_id: UUID) -> dict:
        """Reporte agregado del estado de una materia."""
        data = await self._repo.get_reporte_materia(materia_id)
        alumnos = []
        materia_nombre = ""
        cohorte_id = None
        cohorte_nombre = ""
        for row in data["rows"]:
            entrada = row["EntradaPadron"]
            materia_nombre = row["materia_nombre"]
            cohorte_id = row["cohorte_id"]
            cohorte_nombre = row["cohorte_nombre"]
            umbral_pct = row["umbral_pct"] or 60
            conjunto = row["conjunto_aprobado"] or ["Satisfactorio", "Supera lo esperado"]
            actividades = []
            for calificacion in row["calificaciones"]:
                actividades.append(
                    {
                        "asignacion_id": calificacion.asignacion_id,
                        "asignacion_nombre": None,
                        "estado": "aprobado" if derivar_aprobado(calificacion.nota, umbral_pct, conjunto) else "atrasado",
                        "nota": calificacion.nota,
                        "umbral_pct": umbral_pct,
                    }
                )
            alumnos.append(
                {
                    "usuario_id": entrada.usuario_id,
                    "nombre": f"{entrada.nombre} {entrada.apellidos}",
                    "email": decrypt_entrada_email(entrada),
                    "actividades": actividades,
                }
            )
        return {
            "materia_id": materia_id,
            "materia_nombre": materia_nombre,
            "cohorte_id": cohorte_id,
            "cohorte_nombre": cohorte_nombre,
            "total_alumnos": len(alumnos),
            "alumnos": alumnos,
        }

    async def get_notas_finales(self) -> list[dict]:
        """Notas finales agrupadas por materia."""
        rows = await self._repo.get_notas_finales()
        grouped: dict[UUID, dict] = {}
        for row in rows:
            calificacion: Calificacion = row["Calificacion"]
            item = grouped.setdefault(
                calificacion.materia_id,
                {
                    "materia_id": calificacion.materia_id,
                    "materia_nombre": row["materia_nombre"],
                    "alumnos": set(),
                    "aprobados": set(),
                    "notas_numericas": [],
                },
            )
            item["alumnos"].add(calificacion.usuario_id)
            umbral_pct = row["umbral_pct"] or 60
            conjunto = row["conjunto_aprobado"] or ["Satisfactorio", "Supera lo esperado"]
            if derivar_aprobado(calificacion.nota, umbral_pct, conjunto):
                item["aprobados"].add(calificacion.usuario_id)
            if isinstance(calificacion.nota, int | float):
                item["notas_numericas"].append(float(calificacion.nota))

        result = []
        for item in grouped.values():
            total_alumnos = len(item["alumnos"])
            aprobados = len(item["aprobados"])
            notas = item["notas_numericas"]
            result.append(
                {
                    "materia_id": item["materia_id"],
                    "materia_nombre": item["materia_nombre"],
                    "total_alumnos": total_alumnos,
                    "aprobados": aprobados,
                    "tasa_aprobacion": aprobados / total_alumnos if total_alumnos else 0,
                    "nota_promedio_global": sum(notas) / len(notas) if notas else None,
                }
            )
        return result

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
