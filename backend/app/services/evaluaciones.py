"""Coloquio service (C-14 §6).

Business logic for evaluation convocations and student reservations.
"""

from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluacion import (
    Evaluacion,
    EvaluacionEstado,
    ReservaEvaluacion,
    ReservaEstado,
)
from app.repositories.evaluaciones import get_coloquio_repository
from app.schemas.evaluaciones import (
    ColoquioMetricsResponse,
    DiaSlotSchema,
    EvaluacionCreate,
    EvaluacionMetricsResponse,
    EvaluacionResponse,
    ImportarAlumnosResponse,
    MisReservasItem,
    ReservaCreate,
    ReservaResponse,
    ResultadoConAlumno,
    ResultadoCreate,
    ResultadoResponse,
)


def _generate_dias(fecha_inicio: date, dias_disponibles: int, cupos: int) -> list[dict]:
    return [
        {"fecha": (fecha_inicio + timedelta(days=i)).isoformat(), "cupos": cupos}
        for i in range(dias_disponibles)
    ]


class ColoquioService:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._repo = get_coloquio_repository(session, tenant_id)

    async def create_evaluacion(self, data: EvaluacionCreate) -> EvaluacionResponse:
        if not await self._repo.materia_exists(data.materia_id):
            raise HTTPException(status_code=404, detail="Materia no encontrada")
        if not await self._repo.cohorte_exists(data.cohorte_id):
            raise HTTPException(status_code=404, detail="Cohorte no encontrada")
        if data.dias_disponibles < 1:
            raise HTTPException(status_code=400, detail="dias_disponibles debe ser >= 1")
        if data.cupos < 1:
            raise HTTPException(status_code=400, detail="cupos debe ser >= 1")

        dias = _generate_dias(data.fecha_inicio, data.dias_disponibles, data.cupos)
        evaluacion = await self._repo.create_evaluacion({
            "tenant_id": self._tenant_id,
            "materia_id": data.materia_id,
            "cohorte_id": data.cohorte_id,
            "tipo": data.tipo,
            "instancia": data.instancia,
            "dias_disponibles": data.dias_disponibles,
            "cupos": data.cupos,
            "fecha_inicio": data.fecha_inicio,
            "dias": dias,
            "estado": EvaluacionEstado.ABIERTA,
        })
        return self._to_evaluacion_response(evaluacion)

    async def list_evaluaciones(self) -> list[EvaluacionMetricsResponse]:
        evaluaciones = await self._repo.list_evaluaciones()
        result = []
        for ev in evaluaciones:
            convocados = await self._repo.count_resultados_by_evaluacion(ev.id)
            reservas_activas = await self._repo.count_reservas_activas_by_evaluacion(ev.id)
            total_cupos = ev.dias_disponibles * ev.cupos
            cupos_libres = max(0, total_cupos - reservas_activas)
            result.append(EvaluacionMetricsResponse(
                id=ev.id,
                materia_id=ev.materia_id,
                instancia=ev.instancia,
                estado=ev.estado.value,
                convocados=convocados,
                reservas_activas=reservas_activas,
                cupos_libres=cupos_libres,
            ))
        return result

    async def get_evaluacion(self, evaluacion_id: UUID) -> EvaluacionResponse:
        ev = await self._repo.get_evaluacion(evaluacion_id)
        if ev is None:
            raise HTTPException(status_code=404, detail="Evaluacion no encontrada")
        return self._to_evaluacion_response(ev)

    async def close_evaluacion(self, evaluacion_id: UUID) -> EvaluacionResponse:
        ev = await self._repo.get_evaluacion(evaluacion_id)
        if ev is None:
            raise HTTPException(status_code=404, detail="Evaluacion no encontrada")
        if ev.estado == EvaluacionEstado.CERRADA:
            raise HTTPException(status_code=400, detail="La evaluacion ya esta cerrada")
        ev = await self._repo.update_evaluacion(ev, {"estado": EvaluacionEstado.CERRADA})
        return self._to_evaluacion_response(ev)

    async def importar_alumnos(
        self, evaluacion_id: UUID, alumno_ids: list[UUID]
    ) -> ImportarAlumnosResponse:
        ev = await self._repo.get_evaluacion(evaluacion_id)
        if ev is None:
            raise HTTPException(status_code=404, detail="Evaluacion no encontrada")

        importados = 0
        saltados = 0
        for alumno_id in alumno_ids:
            if not await self._repo.alumno_exists(alumno_id):
                saltados += 1
                continue
            existing = await self._repo.get_resultado(evaluacion_id, alumno_id)
            if existing:
                saltados += 1
                continue
            await self._repo.upsert_resultado(evaluacion_id, alumno_id, "")
            importados += 1

        return ImportarAlumnosResponse(importados=importados, saltados=saltados)

    async def get_metricas(self) -> ColoquioMetricsResponse:
        return ColoquioMetricsResponse(
            total_convocados=await self._repo.total_convocados(),
            total_reservas_activas=await self._repo.total_reservas_activas(),
            total_cupos_libres=await self._repo.total_cupos_libres(),
            instancias_activas=await self._repo.instancias_activas_count(),
        )

    async def create_reserva(
        self, evaluacion_id: UUID, alumno_id: UUID, data: ReservaCreate
    ) -> ReservaResponse:
        ev = await self._repo.get_evaluacion(evaluacion_id)
        if ev is None:
            raise HTTPException(status_code=404, detail="Evaluacion no encontrada")
        if ev.estado == EvaluacionEstado.CERRADA:
            raise HTTPException(status_code=400, detail="La evaluacion esta cerrada")

        dias_fechas = [d["fecha"] for d in ev.dias]
        if data.fecha not in dias_fechas:
            raise HTTPException(status_code=404, detail="Fecha no disponible")

        existing = await self._repo.get_reserva_activa(evaluacion_id, alumno_id)
        if existing:
            raise HTTPException(status_code=409, detail="Ya tienes una reserva activa")

        current_count = await self._repo.count_reservas_activas_by_fecha(evaluacion_id, data.fecha)
        if current_count >= ev.cupos:
            raise HTTPException(status_code=409, detail="Cupo agotado para esta fecha")

        reserva = await self._repo.create_reserva({
            "tenant_id": self._tenant_id,
            "evaluacion_id": evaluacion_id,
            "alumno_id": alumno_id,
            "fecha_reserva": data.fecha,
            "estado": ReservaEstado.ACTIVA,
        })
        return self._to_reserva_response(reserva)

    async def cancel_reserva(self, reserva_id: UUID, alumno_id: UUID) -> ReservaResponse:
        reserva = await self._repo.get_reserva(reserva_id)
        if reserva is None:
            raise HTTPException(status_code=404, detail="Reserva no encontrada")
        if reserva.alumno_id != alumno_id:
            raise HTTPException(status_code=403, detail="No puedes cancelar esta reserva")
        if reserva.estado == ReservaEstado.CANCELADA:
            raise HTTPException(status_code=400, detail="La reserva ya esta cancelada")

        reserva = await self._repo.update_reserva(reserva, {"estado": ReservaEstado.CANCELADA})
        return self._to_reserva_response(reserva)

    async def list_mis_reservas(self, alumno_id: UUID) -> list[MisReservasItem]:
        reservas = await self._repo.list_reservas_by_alumno(alumno_id)
        result = []
        for r in reservas:
            ev = await self._repo.get_evaluacion(r.evaluacion_id)
            materia_nombre = None
            if ev:
                materia_nombre = await self._resolve_materia_nombre(ev.materia_id)
            result.append(MisReservasItem(
                reserva_id=r.id,
                evaluacion_id=r.evaluacion_id,
                materia=materia_nombre,
                instancia=ev.instancia if ev else "",
                fecha_reserva=r.fecha_reserva,
                estado=r.estado.value,
            ))
        return result

    async def list_reservas_by_evaluacion(
        self, evaluacion_id: UUID
    ) -> list[ReservaResponse]:
        reservas = await self._repo.list_reservas_by_evaluacion(evaluacion_id)
        return [self._to_reserva_response(r) for r in reservas]

    async def upsert_resultado(
        self, evaluacion_id: UUID, data: ResultadoCreate
    ) -> ResultadoResponse:
        ev = await self._repo.get_evaluacion(evaluacion_id)
        if ev is None:
            raise HTTPException(status_code=404, detail="Evaluacion no encontrada")
        if not await self._repo.alumno_exists(data.alumno_id):
            raise HTTPException(status_code=404, detail="Alumno no encontrado")

        resultado = await self._repo.upsert_resultado(evaluacion_id, data.alumno_id, data.nota_final)
        return ResultadoResponse(
            id=resultado.id,
            tenant_id=resultado.tenant_id,
            evaluacion_id=resultado.evaluacion_id,
            alumno_id=resultado.alumno_id,
            nota_final=resultado.nota_final,
            created_at=resultado.created_at,
            updated_at=resultado.updated_at,
        )

    async def list_resultados(self, evaluacion_id: UUID) -> list[ResultadoConAlumno]:
        ev = await self._repo.get_evaluacion(evaluacion_id)
        if ev is None:
            raise HTTPException(status_code=404, detail="Evaluacion no encontrada")

        resultados = await self._repo.list_resultados_by_evaluacion(evaluacion_id)
        result = []
        for r in resultados:
            alumno_nombre = await self._resolve_alumno_nombre(r.alumno_id)
            reserva_estado = None
            reserva = await self._repo.get_reserva_activa(evaluacion_id, r.alumno_id)
            if reserva:
                reserva_estado = reserva.estado.value
            result.append(ResultadoConAlumno(
                id=r.id,
                alumno_id=r.alumno_id,
                alumno_nombre=alumno_nombre,
                nota_final=r.nota_final,
                estado_reserva=reserva_estado,
            ))
        return result

    async def _resolve_materia_nombre(self, materia_id: UUID) -> str | None:
        from app.models.materia import Materia
        from sqlalchemy import select
        stmt = select(Materia.nombre).where(
            Materia.id == materia_id,
            Materia.tenant_id == self._tenant_id,
        )
        result = await self._session.execute(stmt)
        row = result.one_or_none()
        return row.nombre if row else None

    async def _resolve_alumno_nombre(self, alumno_id: UUID) -> str | None:
        from app.models.usuario import Usuario
        from sqlalchemy import select
        stmt = select(Usuario.nombre, Usuario.apellidos).where(
            Usuario.id == alumno_id,
            Usuario.tenant_id == self._tenant_id,
        )
        result = await self._session.execute(stmt)
        row = result.one_or_none()
        return f"{row.nombre} {row.apellidos}" if row else None

    def _to_evaluacion_response(self, ev: Evaluacion) -> EvaluacionResponse:
        dias = [DiaSlotSchema(fecha=d["fecha"], cupos=d["cupos"]) for d in ev.dias]
        return EvaluacionResponse(
            id=ev.id,
            tenant_id=ev.tenant_id,
            materia_id=ev.materia_id,
            cohorte_id=ev.cohorte_id,
            tipo=ev.tipo.value,
            instancia=ev.instancia,
            dias_disponibles=ev.dias_disponibles,
            cupos=ev.cupos,
            fecha_inicio=ev.fecha_inicio,
            dias=dias,
            estado=ev.estado.value,
            created_at=ev.created_at,
            updated_at=ev.updated_at,
        )

    def _to_reserva_response(self, r: ReservaEvaluacion) -> ReservaResponse:
        return ReservaResponse(
            id=r.id,
            tenant_id=r.tenant_id,
            evaluacion_id=r.evaluacion_id,
            alumno_id=r.alumno_id,
            fecha_reserva=r.fecha_reserva,
            estado=r.estado.value,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )