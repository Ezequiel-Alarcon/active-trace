"""Equipos docentes router (C-08).

Endpoints batch sobre asignaciones: mis-equipos, asignacion masiva,
clonar entre cohortes, vigencia general y export CSV.
Todos requieren permiso equipos:asignar.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_user
from app.core.dependencies import get_db
from app.core.permissions import require_permission
from app.schemas.equipos import (
    AsignacionMasivaRequest,
    AsignacionMasivaResponse,
    ClonarEquipoRequest,
    ClonarEquipoResponse,
    EquipoAsignacionResponse,
    VigenciaEquipoRequest,
    VigenciaEquipoResponse,
)
from app.services.equipos import EquipoService

equipo_router = APIRouter(prefix="/api/equipos", tags=["equipos"])

PERM = "equipos:asignar"


async def _get_equipo_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> EquipoService:
    return EquipoService(db, current_user.tenant_id)


# ── mis-equipos ────────────────────────────────────────────────────────

@equipo_router.get(
    "/mis-equipos",
    response_model=list[EquipoAsignacionResponse],
    summary="Mis equipos — asignaciones del usuario autenticado",
    dependencies=[Depends(require_permission(PERM))],
)
async def mis_equipos(
    request: Request,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[EquipoService, Depends(_get_equipo_service)],
    cohorte_id: UUID | None = None,
    materia_id: UUID | None = None,
    estado_vigencia: str | None = None,
) -> list:
    return await service.mis_equipos(
        current_user.user_id,
        cohorte_id=cohorte_id,
        materia_id=materia_id,
        estado_vigencia=estado_vigencia,
    )


# ── asignacion-masiva ──────────────────────────────────────────────────

@equipo_router.post(
    "/asignacion-masiva",
    response_model=AsignacionMasivaResponse,
    summary="Asignacion masiva de docentes a un equipo",
    dependencies=[Depends(require_permission(PERM))],
)
async def asignacion_masiva(
    request: Request,
    data: AsignacionMasivaRequest,
    service: Annotated[EquipoService, Depends(_get_equipo_service)],
):
    return await service.asignacion_masiva(data)


# ── clonar ─────────────────────────────────────────────────────────────

@equipo_router.post(
    "/clonar",
    response_model=ClonarEquipoResponse,
    summary="Clonar equipo docente entre cohortes",
    dependencies=[Depends(require_permission(PERM))],
)
async def clonar_equipo(
    request: Request,
    data: ClonarEquipoRequest,
    service: Annotated[EquipoService, Depends(_get_equipo_service)],
):
    return await service.clonar_equipo(data)


# ── vigencia ───────────────────────────────────────────────────────────

@equipo_router.patch(
    "/vigencia",
    response_model=VigenciaEquipoResponse,
    summary="Modificar vigencia general del equipo",
    dependencies=[Depends(require_permission(PERM))],
)
async def modificar_vigencia(
    request: Request,
    data: VigenciaEquipoRequest,
    service: Annotated[EquipoService, Depends(_get_equipo_service)],
):
    return await service.modificar_vigencia(data)


# ── exportar ───────────────────────────────────────────────────────────

@equipo_router.get(
    "/exportar",
    summary="Exportar equipo docente a CSV",
    dependencies=[Depends(require_permission(PERM))],
)
async def exportar_equipo(
    request: Request,
    service: Annotated[EquipoService, Depends(_get_equipo_service)],
    materia_id: UUID = Query(...),
    cohorte_id: UUID = Query(...),
    rol_id: UUID | None = None,
):
    rows = await service.exportar_equipo_data(materia_id, cohorte_id, rol_id=rol_id)
    csv_content = service.generate_csv(rows)

    materia = await service._get_materia(materia_id)
    cohorte = await service._get_cohorte(cohorte_id)
    nombre_materia = materia.nombre if materia else "materia"
    nombre_cohorte = cohorte.nombre if cohorte else "cohorte"
    # Sanitize filename parts
    safe_materia = "".join(c for c in nombre_materia if c.isalnum() or c in ("_", "-"))[:32]
    safe_cohorte = "".join(c for c in nombre_cohorte if c.isalnum() or c in ("_", "-"))[:32]
    filename = f"equipo_{safe_materia}_{safe_cohorte}.csv"

    return Response(
        content=csv_content.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
