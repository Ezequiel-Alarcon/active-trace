"""Programas y Fechas Academicas router (C-17 §4).

All endpoints require estructura:gestionar permission.
Mounted at /api in app/api/v1/main_router.py.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_user
from app.core.dependencies import get_db
from app.core.permissions import require_permission
from app.schemas.programas_fechas import (
    FechaAcademicaCreate,
    FechaAcademicaResponse,
    FechaAcademicaUpdate,
    FragmentoLmsResponse,
    ProgramaCreate,
    ProgramaResponse,
    ProgramaUpdate,
)
from app.services.programas_fechas import ProgramaFechasService

router = APIRouter(prefix="/api", tags=["programas", "fechas"])

PERM = "estructura:gestionar"


async def _get_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> ProgramaFechasService:
    return ProgramaFechasService(db, current_user.tenant_id)


# ── Programas ─────────────────────────────────────────────────────────

@router.get(
    "/programas",
    response_model=list[ProgramaResponse],
    summary="List programas",
    dependencies=[Depends(require_permission(PERM))],
)
async def list_programas(
    request: Request,
    service: Annotated[ProgramaFechasService, Depends(_get_service)],
    materia_id: UUID | None = Query(None),
    carrera_id: UUID | None = Query(None),
    cohorte_id: UUID | None = Query(None),
) -> list:
    return await service.list_programas(
        materia_id=materia_id,
        carrera_id=carrera_id,
        cohorte_id=cohorte_id,
    )


@router.post(
    "/programas",
    response_model=ProgramaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create programa",
    dependencies=[Depends(require_permission(PERM))],
)
async def create_programa(
    request: Request,
    data: ProgramaCreate,
    service: Annotated[ProgramaFechasService, Depends(_get_service)],
):
    return await service.create_programa(data)


@router.get(
    "/programas/{programa_id}",
    response_model=ProgramaResponse,
    summary="Get programa by id",
    dependencies=[Depends(require_permission(PERM))],
)
async def get_programa(
    request: Request,
    programa_id: UUID,
    service: Annotated[ProgramaFechasService, Depends(_get_service)],
):
    return await service.get_programa(programa_id)


@router.patch(
    "/programas/{programa_id}",
    response_model=ProgramaResponse,
    summary="Update programa",
    dependencies=[Depends(require_permission(PERM))],
)
async def update_programa(
    request: Request,
    programa_id: UUID,
    data: ProgramaUpdate,
    service: Annotated[ProgramaFechasService, Depends(_get_service)],
):
    return await service.update_programa(programa_id, data)


@router.delete(
    "/programas/{programa_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Soft-delete programa",
    dependencies=[Depends(require_permission(PERM))],
)
async def delete_programa(
    request: Request,
    programa_id: UUID,
    service: Annotated[ProgramaFechasService, Depends(_get_service)],
) -> None:
    await service.delete_programa(programa_id)


# ── Fechas Academicas ─────────────────────────────────────────────────

@router.get(
    "/fechas-academicas",
    response_model=list[FechaAcademicaResponse],
    summary="List fechas academicas",
    dependencies=[Depends(require_permission(PERM))],
)
async def list_fechas(
    request: Request,
    service: Annotated[ProgramaFechasService, Depends(_get_service)],
    materia_id: UUID | None = Query(None),
    cohorte_id: UUID | None = Query(None),
    tipo: str | None = Query(None),
) -> list:
    return await service.list_fechas(
        materia_id=materia_id,
        cohorte_id=cohorte_id,
        tipo=tipo,
    )


@router.post(
    "/fechas-academicas",
    response_model=FechaAcademicaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create fecha academica",
    dependencies=[Depends(require_permission(PERM))],
)
async def create_fecha(
    request: Request,
    data: FechaAcademicaCreate,
    service: Annotated[ProgramaFechasService, Depends(_get_service)],
):
    return await service.create_fecha(data)


@router.get(
    "/fechas-academicas/{fecha_id}",
    response_model=FechaAcademicaResponse,
    summary="Get fecha academica by id",
    dependencies=[Depends(require_permission(PERM))],
)
async def get_fecha(
    request: Request,
    fecha_id: UUID,
    service: Annotated[ProgramaFechasService, Depends(_get_service)],
):
    return await service.get_fecha(fecha_id)


@router.patch(
    "/fechas-academicas/{fecha_id}",
    response_model=FechaAcademicaResponse,
    summary="Update fecha academica",
    dependencies=[Depends(require_permission(PERM))],
)
async def update_fecha(
    request: Request,
    fecha_id: UUID,
    data: FechaAcademicaUpdate,
    service: Annotated[ProgramaFechasService, Depends(_get_service)],
):
    return await service.update_fecha(fecha_id, data)


@router.delete(
    "/fechas-academicas/{fecha_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Soft-delete fecha academica",
    dependencies=[Depends(require_permission(PERM))],
)
async def delete_fecha(
    request: Request,
    fecha_id: UUID,
    service: Annotated[ProgramaFechasService, Depends(_get_service)],
) -> None:
    await service.delete_fecha(fecha_id)


# ── Fragmento LMS ─────────────────────────────────────────────────────

@router.get(
    "/fechas-academicas/fragmento-lms",
    response_class=HTMLResponse,
    summary="Generate LMS HTML fragment with fechas",
    dependencies=[Depends(require_permission(PERM))],
)
async def fragmento_lms(
    request: Request,
    service: Annotated[ProgramaFechasService, Depends(_get_service)],
    materia_id: UUID = Query(...),
    cohorte_id: UUID = Query(...),
):
    html = await service.generar_fragmento_lms(materia_id, cohorte_id)
    return HTMLResponse(content=html)
