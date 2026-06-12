"""Coloquios router (C-14 §7).

Endpoints for evaluation colloquium management:
- COORDINADOR/ADMIN: create, list, import, close, view results
- ALUMNO: reserve slot, cancel reservation, view own reservations
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_user
from app.core.dependencies import get_db
from app.core.permissions import require_permission
from app.schemas.evaluaciones import (
    ColoquioMetricsResponse,
    EvaluacionCreate,
    EvaluacionListResponse,
    EvaluacionResponse,
    ImportarAlumnosRequest,
    ImportarAlumnosResponse,
    MisReservasItem,
    ReservaCreate,
    ReservaResponse,
    ResultadoConAlumno,
    ResultadoCreate,
    ResultadoResponse,
)
from app.services.evaluaciones import ColoquioService

router = APIRouter(prefix="/api/coloquios", tags=["coloquios"])

PERM_GESTIONAR = "coloquios:gestionar"
PERM_VER = "coloquios:ver"
PERM_RESERVAR = "coloquios:reservar"


def _get_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    request: Request,
) -> ColoquioService:
    return ColoquioService(db, current_user.tenant_id)


# ── Coordinator/Admin endpoints ───────────────────────────────────────

@router.post(
    "/",
    response_model=EvaluacionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create evaluation convocation",
    dependencies=[Depends(require_permission(PERM_GESTIONAR))],
)
async def create_evaluacion(
    data: EvaluacionCreate,
    service: Annotated[ColoquioService, Depends(_get_service)],
):
    return await service.create_evaluacion(data)


@router.get(
    "/",
    response_model=EvaluacionListResponse,
    summary="List all evaluation convocations",
    dependencies=[Depends(require_permission(PERM_VER))],
)
async def list_evaluaciones(
    service: Annotated[ColoquioService, Depends(_get_service)],
):
    evaluaciones = await service.list_evaluaciones()
    return EvaluacionListResponse(evaluaciones=evaluaciones)


@router.get(
    "/metricas",
    response_model=ColoquioMetricsResponse,
    summary="Get aggregated metrics",
    dependencies=[Depends(require_permission(PERM_VER))],
)
async def get_metricas(
    service: Annotated[ColoquioService, Depends(_get_service)],
):
    return await service.get_metricas()


@router.get(
    "/{evaluacion_id}",
    response_model=EvaluacionResponse,
    summary="Get evaluation by id",
    dependencies=[Depends(require_permission(PERM_VER))],
)
async def get_evaluacion(
    evaluacion_id: UUID,
    service: Annotated[ColoquioService, Depends(_get_service)],
):
    return await service.get_evaluacion(evaluacion_id)


@router.post(
    "/{evaluacion_id}/importar",
    response_model=ImportarAlumnosResponse,
    status_code=status.HTTP_200_OK,
    summary="Import students to convocation",
    dependencies=[Depends(require_permission(PERM_GESTIONAR))],
)
async def importar_alumnos(
    evaluacion_id: UUID,
    data: ImportarAlumnosRequest,
    service: Annotated[ColoquioService, Depends(_get_service)],
):
    return await service.importar_alumnos(evaluacion_id, data.alumno_ids)


@router.patch(
    "/{evaluacion_id}/cerrar",
    response_model=EvaluacionResponse,
    summary="Close evaluation convocation",
    dependencies=[Depends(require_permission(PERM_GESTIONAR))],
)
async def close_evaluacion(
    evaluacion_id: UUID,
    service: Annotated[ColoquioService, Depends(_get_service)],
):
    return await service.close_evaluacion(evaluacion_id)


@router.get(
    "/{evaluacion_id}/reservas",
    response_model=list[ReservaResponse],
    summary="List all reservations for an evaluation",
    dependencies=[Depends(require_permission(PERM_VER))],
)
async def list_reservas(
    evaluacion_id: UUID,
    service: Annotated[ColoquioService, Depends(_get_service)],
):
    return await service.list_reservas_by_evaluacion(evaluacion_id)


@router.post(
    "/{evaluacion_id}/resultados",
    response_model=ResultadoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record result for a student",
    dependencies=[Depends(require_permission(PERM_GESTIONAR))],
)
async def upsert_resultado(
    evaluacion_id: UUID,
    data: ResultadoCreate,
    service: Annotated[ColoquioService, Depends(_get_service)],
):
    return await service.upsert_resultado(evaluacion_id, data)


@router.get(
    "/{evaluacion_id}/resultados",
    response_model=list[ResultadoConAlumno],
    summary="List consolidated results for an evaluation",
    dependencies=[Depends(require_permission(PERM_VER))],
)
async def list_resultados(
    evaluacion_id: UUID,
    service: Annotated[ColoquioService, Depends(_get_service)],
):
    return await service.list_resultados(evaluacion_id)


# ── Student endpoints ─────────────────────────────────────────────────

@router.post(
    "/{evaluacion_id}/reservas",
    response_model=ReservaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Reserve a slot",
    dependencies=[Depends(require_permission(PERM_RESERVAR))],
)
async def create_reserva(
    evaluacion_id: UUID,
    data: ReservaCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[ColoquioService, Depends(_get_service)],
):
    return await service.create_reserva(evaluacion_id, current_user.user_id, data)


@router.get(
    "/mis-reservas",
    response_model=list[MisReservasItem],
    summary="List my reservations",
    dependencies=[Depends(require_permission(PERM_RESERVAR))],
)
async def list_mis_reservas(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[ColoquioService, Depends(_get_service)],
):
    return await service.list_mis_reservas(current_user.user_id)


@router.patch(
    "/reservas/{reserva_id}/cancelar",
    response_model=ReservaResponse,
    summary="Cancel a reservation",
    dependencies=[Depends(require_permission(PERM_RESERVAR))],
)
async def cancel_reserva(
    reserva_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[ColoquioService, Depends(_get_service)],
):
    return await service.cancel_reserva(reserva_id, current_user.user_id)