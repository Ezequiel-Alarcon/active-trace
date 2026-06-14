from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_user
from app.core.dependencies import get_db
from app.core.permissions import require_permission
from app.schemas.avisos import (
    AcknowledgmentStatusResponse,
    AvisoCreate,
    AvisoListResponse,
    AvisoResponse,
    AvisoUpdate,
)
from app.services.avisos import AvisoService

router = APIRouter(prefix="/api/avisos", tags=["avisos"])

PERM_PUBLICAR = "avisos:publicar"
PERM_CONFIRMAR = "avisos:confirmar"


def _get_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> AvisoService:
    return AvisoService(db, current_user.tenant_id)


# ── CRUD (avisos:publicar) ─────────────────────────────────────────────

@router.post(
    "/",
    response_model=AvisoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create aviso",
    dependencies=[Depends(require_permission(PERM_PUBLICAR))],
)
async def create_aviso(
    data: AvisoCreate,
    service: Annotated[AvisoService, Depends(_get_service)],
):
    return await service.create(data)


@router.get(
    "/",
    response_model=AvisoListResponse,
    summary="List all avisos for management",
    dependencies=[Depends(require_permission(PERM_PUBLICAR))],
)
async def list_avisos(
    service: Annotated[AvisoService, Depends(_get_service)],
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    alcance: str | None = None,
):
    items, total = await service.list_all(page=page, per_page=per_page, alcance=alcance)
    return AvisoListResponse(items=items, total=total, page=page, per_page=per_page)


@router.get(
    "/{aviso_id}",
    response_model=AvisoResponse,
    summary="Get aviso by id",
    dependencies=[Depends(require_permission(PERM_PUBLICAR))],
)
async def get_aviso(
    aviso_id: UUID,
    service: Annotated[AvisoService, Depends(_get_service)],
):
    return await service.get(aviso_id)


@router.patch(
    "/{aviso_id}",
    response_model=AvisoResponse,
    summary="Update aviso",
    dependencies=[Depends(require_permission(PERM_PUBLICAR))],
)
async def update_aviso(
    aviso_id: UUID,
    data: AvisoUpdate,
    service: Annotated[AvisoService, Depends(_get_service)],
):
    return await service.update(aviso_id, data)


@router.delete(
    "/{aviso_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete aviso",
    dependencies=[Depends(require_permission(PERM_PUBLICAR))],
)
async def delete_aviso(
    aviso_id: UUID,
    service: Annotated[AvisoService, Depends(_get_service)],
):
    await service.delete(aviso_id)


# ── User visible + acknowledgment (avisos:confirmar) ────────────────────

@router.get(
    "/mis-avisos",
    response_model=list[AvisoResponse],
    summary="List avisos visible to the authenticated user",
    dependencies=[Depends(require_permission(PERM_CONFIRMAR))],
)
async def mis_avisos(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[AvisoService, Depends(_get_service)],
):
    return await service.list_visible(
        user_id=current_user.user_id,
        user_roles=[],
    )


@router.post(
    "/{aviso_id}/acknowledge",
    status_code=status.HTTP_201_CREATED,
    summary="Acknowledge an aviso",
    dependencies=[Depends(require_permission(PERM_CONFIRMAR))],
)
async def acknowledge_aviso(
    aviso_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[AvisoService, Depends(_get_service)],
):
    await service.acknowledge(aviso_id, current_user.user_id)


@router.get(
    "/{aviso_id}/acknowledgment",
    response_model=AcknowledgmentStatusResponse,
    summary="Get acknowledgment status for an aviso",
    dependencies=[Depends(require_permission(PERM_CONFIRMAR))],
)
async def acknowledgment_status(
    aviso_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[AvisoService, Depends(_get_service)],
):
    return await service.get_acknowledgment_status(aviso_id, current_user.user_id)
