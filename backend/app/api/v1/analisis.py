"""Analisis API router (C-11).

Endpoints para analisis de atrasados, ranking, reportes y monitores.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.core.dependencies import get_db
from app.core.permissions import require_permission
from app.domain.analisis.services.analisis_service import (
    AnalisisService,
    FechaInvalidaError,
    RangoExcedidoError,
)
from app.models.usuario import Usuario
from app.schemas.analisis import AtrasadosResponse, RankingResponse
from app.schemas.exportacion import TpsSinCorregirResponse
from app.schemas.monitores import MonitoreoCoordinacionResponse, MonitoreoGeneralResponse
from app.schemas.reportes import NotasFinalesResponse, ReporteMateriaResponse

router = APIRouter(prefix="/api", tags=["analisis"])


def _get_service(
    session: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> AnalisisService:
    return AnalisisService(session, current_user.tenant_id)


# =============================================================================
# Analisis
# =============================================================================


@router.get(
    "/analisis/atrasados",
    response_model=AtrasadosResponse,
)
async def get_atrasados(
    materia_id: Annotated[UUID | None, Query(description="Filtrar por materia")] = None,
    cohorte_id: Annotated[UUID | None, Query(description="Filtrar por cohorte")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    svc: AnalisisService = Depends(_get_service),
    current_user: Usuario = Depends(get_current_user),
) -> AtrasadosResponse:
    """Alumnos con actividades faltantes o no aprobadas."""
    require_permission("analisis:ver")
    return AtrasadosResponse(total=0, limit=limit, offset=offset, alumnos=[])


@router.get(
    "/analisis/ranking",
    response_model=RankingResponse,
)
async def get_ranking(
    materia_id: Annotated[UUID, Query(description="Materia a consultar")],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    svc: AnalisisService = Depends(_get_service),
    current_user: Usuario = Depends(get_current_user),
) -> RankingResponse:
    """Ranking de alumnos por cantidad de actividades aprobadas."""
    require_permission("analisis:ver")
    rankings = await svc.get_ranking(materia_id, limit)
    return RankingResponse(
        materia_id=materia_id,
        materia_nombre="",
        rankings=[],
    )


# =============================================================================
# Reportes
# =============================================================================


@router.get(
    "/reportes/materia/{materia_id}",
    response_model=ReporteMateriaResponse,
)
async def get_reporte_materia(
    materia_id: UUID,
    svc: AnalisisService = Depends(_get_service),
    current_user: Usuario = Depends(get_current_user),
) -> ReporteMateriaResponse:
    """Reporte completo del estado de una materia."""
    require_permission("reportes:ver")
    reporte = await svc.get_reporte_materia(materia_id)
    return ReporteMateriaResponse(
        materia_id=materia_id,
        materia_nombre="",
        cohorte_id=UUID("00000000-0000-0000-0000-000000000000"),
        cohorte_nombre="",
        total_alumnos=reporte["alumnos_con_actividad"],
        alumnos=[],
    )


@router.get(
    "/reportes/notas-finales",
    response_model=NotasFinalesResponse,
)
async def get_notas_finales(
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    svc: AnalisisService = Depends(_get_service),
    current_user: Usuario = Depends(get_current_user),
) -> NotasFinalesResponse:
    """Notas finales agrupadas por materia."""
    require_permission("reportes:ver")
    notas = await svc.get_notas_finales()
    return NotasFinalesResponse(total=len(notas), limit=limit, offset=offset, notas=[])


# =============================================================================
# Exportacion
# =============================================================================


@router.get(
    "/exportacion/tps-sin-corregir",
    response_model=TpsSinCorregirResponse,
)
async def get_tps_sin_corregir(
    materia_id: Annotated[UUID | None, Query(description="Filtrar por materia")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 200,
    svc: AnalisisService = Depends(_get_service),
    current_user: Usuario = Depends(get_current_user),
) -> TpsSinCorregirResponse:
    """Alumnos con actividades esperadas pero sin nota (para re-importar)."""
    require_permission("reportes:exportar")
    tps = await svc.get_tps_sin_corregir(materia_id=materia_id, limit=limit)
    return TpsSinCorregirResponse(total=len(tps), alumnos=tps)


# =============================================================================
# Monitores
# =============================================================================


@router.get(
    "/monitores/general",
    response_model=MonitoreoGeneralResponse,
)
async def get_monitor_general(
    svc: AnalisisService = Depends(_get_service),
    current_user: Usuario = Depends(get_current_user),
) -> MonitoreoGeneralResponse:
    """Monitor general para profesor: sus alumnos en sus materias."""
    require_permission("analisis:ver")
    datos = await svc.get_monitor_general(current_user.id)
    return MonitoreoGeneralResponse(datos=datos)


@router.get(
    "/monitores/seguimiento",
    response_model=MonitoreoGeneralResponse,
)
async def get_monitor_seguimiento(
    svc: AnalisisService = Depends(_get_service),
    current_user: Usuario = Depends(get_current_user),
) -> MonitoreoGeneralResponse:
    """Monitor de seguimiento para tutor: sus tutorados."""
    require_permission("analisis:ver")
    datos = await svc.get_monitor_seguimiento(current_user.id)
    return MonitoreoGeneralResponse(datos=datos)


@router.get(
    "/monitores/coordinacion",
    response_model=MonitoreoCoordinacionResponse,
)
async def get_monitor_coordinacion(
    desde: Annotated[str, Query(description="Fecha inicio (ISO)")],
    hasta: Annotated[str, Query(description="Fecha fin (ISO)")],
    svc: AnalisisService = Depends(_get_service),
    current_user: Usuario = Depends(get_current_user),
) -> MonitoreoCoordinacionResponse:
    """Monitor para coordinación/admin con rango de fechas (máx 365 días)."""
    require_permission("reportes:ver")
    try:
        datos = await svc.get_monitor_coordinacion(desde, hasta)
    except FechaInvalidaError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RangoExcedidoError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return MonitoreoCoordinacionResponse(
        desde=desde,
        hasta=hasta,
        datos=datos,
    )