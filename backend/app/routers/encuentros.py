"""Encuentros router (C-18 §7).

# TODO: (TEST) C-13 no tiene tests. Ni encuentros ni guardias tienen
# archivos test_encuentro* o test_guardia*. Agregar cobertura.

Endpoints for SlotEncuentro and InstanciaEncuentro CRUD, plus
fragmento LMS generation.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_user
from app.core.dependencies import get_db
from app.core.permissions import require_permission
from app.schemas.encuentros import (
    InstanciaEncuentroCreate,
    InstanciaEncuentroResponse,
    InstanciaEncuentroUpdate,
    SlotEncuentroCreate,
    SlotEncuentroResponse,
    SlotEncuentroUpdate,
)
from app.services.encuentros import EncuentrosService

router = APIRouter(prefix="/api/encuentros", tags=["encuentros"])

PERM = "encuentros:gestionar"


async def _get_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> EncuentrosService:
    return EncuentrosService(db, current_user.tenant_id)


# ── Slots ─────────────────────────────────────────────────────────────

@router.get(
    "/slots",
    response_model=list[SlotEncuentroResponse],
    summary="List slots de encuentro",
    dependencies=[Depends(require_permission(PERM))],
)
async def list_slots(
    request: Request,
    service: Annotated[EncuentrosService, Depends(_get_service)],
    materia_id: UUID | None = Query(None),
    cohorte_id: UUID | None = Query(None),
) -> list:
    return await service.list_slots(materia_id=materia_id, cohorte_id=cohorte_id)


@router.post(
    "/slots",
    response_model=SlotEncuentroResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create slot de encuentro recurrente",
    dependencies=[Depends(require_permission(PERM))],
)
async def create_slot(
    request: Request,
    data: SlotEncuentroCreate,
    service: Annotated[EncuentrosService, Depends(_get_service)],
):
    return await service.create_slot(data)


@router.get(
    "/slots/{slot_id}",
    response_model=SlotEncuentroResponse,
    summary="Get slot by id",
    dependencies=[Depends(require_permission(PERM))],
)
async def get_slot(
    request: Request,
    slot_id: UUID,
    service: Annotated[EncuentrosService, Depends(_get_service)],
):
    return await service.get_slot(slot_id)


@router.patch(
    "/slots/{slot_id}",
    response_model=SlotEncuentroResponse,
    summary="Update slot",
    dependencies=[Depends(require_permission(PERM))],
)
async def update_slot(
    request: Request,
    slot_id: UUID,
    data: SlotEncuentroUpdate,
    service: Annotated[EncuentrosService, Depends(_get_service)],
):
    return await service.update_slot(slot_id, data)


@router.delete(
    "/slots/{slot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Soft-delete slot",
    dependencies=[Depends(require_permission(PERM))],
)
async def delete_slot(
    request: Request,
    slot_id: UUID,
    service: Annotated[EncuentrosService, Depends(_get_service)],
) -> None:
    await service.delete_slot(slot_id)


# ── Instancias ────────────────────────────────────────────────────────

@router.get(
    "/instancias",
    response_model=list[InstanciaEncuentroResponse],
    summary="List instances de encuentro",
    dependencies=[Depends(require_permission(PERM))],
)
async def list_instancias(
    request: Request,
    service: Annotated[EncuentrosService, Depends(_get_service)],
    materia_id: UUID | None = Query(None),
    cohorte_id: UUID | None = Query(None),
    estado: str | None = Query(None),
    fecha_desde: str | None = Query(None),
    fecha_hasta: str | None = Query(None),
) -> list:
    from datetime import date
    fd = date.fromisoformat(fecha_desde) if fecha_desde else None
    fh = date.fromisoformat(fecha_hasta) if fecha_hasta else None
    return await service.list_instancias(
        materia_id=materia_id,
        cohorte_id=cohorte_id,
        estado=estado,
        fecha_desde=fd,
        fecha_hasta=fh,
    )


@router.post(
    "/instancias/unico",
    response_model=InstanciaEncuentroResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create encuentro unico (sin slot)",
    dependencies=[Depends(require_permission(PERM))],
)
async def create_instancia_unica(
    request: Request,
    data: InstanciaEncuentroCreate,
    service: Annotated[EncuentrosService, Depends(_get_service)],
):
    return await service.create_instancia_unica(data)


@router.get(
    "/instancias/{instancia_id}",
    response_model=InstanciaEncuentroResponse,
    summary="Get instancia by id",
    dependencies=[Depends(require_permission(PERM))],
)
async def get_instancia(
    request: Request,
    instancia_id: UUID,
    service: Annotated[EncuentrosService, Depends(_get_service)],
):
    return await service.get_instancia(instancia_id)


@router.patch(
    "/instancias/{instancia_id}",
    response_model=InstanciaEncuentroResponse,
    summary="Update instancia",
    dependencies=[Depends(require_permission(PERM))],
)
async def update_instancia(
    request: Request,
    instancia_id: UUID,
    data: InstanciaEncuentroUpdate,
    service: Annotated[EncuentrosService, Depends(_get_service)],
):
    return await service.update_instancia(instancia_id, data)


@router.delete(
    "/instancias/{instancia_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Soft-delete instancia",
    dependencies=[Depends(require_permission(PERM))],
)
async def delete_instancia(
    request: Request,
    instancia_id: UUID,
    service: Annotated[EncuentrosService, Depends(_get_service)],
) -> None:
    await service.delete_instancia(instancia_id)


# ── Fragmento LMS ─────────────────────────────────────────────────────

@router.get(
    "/instancias/fragmento-lms",
    response_class=HTMLResponse,
    summary="Generate LMS HTML fragment with instancias",
    dependencies=[Depends(require_permission(PERM))],
)
async def fragmento_lms(
    request: Request,
    service: Annotated[EncuentrosService, Depends(_get_service)],
    materia_id: UUID = Query(...),
    cohorte_id: UUID = Query(...),
):
    html = await service.generar_fragmento_lms(materia_id, cohorte_id)
    return HTMLResponse(content=html)
