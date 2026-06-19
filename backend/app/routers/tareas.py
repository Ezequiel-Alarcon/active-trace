from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_user, resolve_user_roles
from app.core.dependencies import get_db
from app.core.permissions import require_permission
from app.schemas.tareas import (
    ComentarioCreate,
    ComentarioListResponse,
    ComentarioResponse,
    TareaCreate,
    TareaListResponse,
    TareaResponse,
    TareaUpdate,
)
from app.services.tareas import TareaService

router = APIRouter(prefix="/api/tareas", tags=["tareas"])

PERM_GESTIONAR = "tareas:gestionar"


def _get_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> TareaService:
    return TareaService(db, current_user.tenant_id)


@router.post(
    "/",
    response_model=TareaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create tarea interna",
    dependencies=[Depends(require_permission(PERM_GESTIONAR))],
)
async def create_tarea(
    data: TareaCreate,
    service: Annotated[TareaService, Depends(_get_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    roles = await resolve_user_roles(db, current_user.user_id, current_user.tenant_id)
    return await service.create(data, user_id=current_user.user_id, roles=roles)


@router.get(
    "/mis-tareas",
    response_model=TareaListResponse,
    summary="List my own tareas",
    dependencies=[Depends(require_permission(PERM_GESTIONAR))],
)
async def mis_tareas(
    service: Annotated[TareaService, Depends(_get_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    estado: str | None = None,
    materia_id: UUID | None = None,
):
    items, total = await service.list_mis_tareas(
        current_user.user_id,
        page=page,
        per_page=per_page,
        estado=estado,
        materia_id=materia_id,
    )
    return TareaListResponse(items=items, total=total, page=page, per_page=per_page)


@router.get(
    "/",
    response_model=TareaListResponse,
    summary="List all tareas (admin/coord only)",
    dependencies=[Depends(require_permission(PERM_GESTIONAR))],
)
async def list_tareas(
    service: Annotated[TareaService, Depends(_get_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    estado: str | None = None,
    materia_id: UUID | None = None,
    asignado_a: UUID | None = None,
    q: str | None = None,
):
    roles = await resolve_user_roles(db, current_user.user_id, current_user.tenant_id)
    items, total = await service.list_all(
        user_id=current_user.user_id,
        roles=roles,
        page=page,
        per_page=per_page,
        estado=estado,
        materia_id=materia_id,
        asignado_a=asignado_a,
        q=q,
    )
    return TareaListResponse(items=items, total=total, page=page, per_page=per_page)


@router.get(
    "/{tarea_id}",
    response_model=TareaResponse,
    summary="Get tarea by id",
    dependencies=[Depends(require_permission(PERM_GESTIONAR))],
)
async def get_tarea(
    tarea_id: UUID,
    service: Annotated[TareaService, Depends(_get_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    roles = await resolve_user_roles(db, current_user.user_id, current_user.tenant_id)
    return await service.get(tarea_id, user_id=current_user.user_id, roles=roles)


@router.patch(
    "/{tarea_id}",
    response_model=TareaResponse,
    summary="Update tarea (estado or descripcion)",
    dependencies=[Depends(require_permission(PERM_GESTIONAR))],
)
async def update_tarea(
    tarea_id: UUID,
    data: TareaUpdate,
    service: Annotated[TareaService, Depends(_get_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    roles = await resolve_user_roles(db, current_user.user_id, current_user.tenant_id)
    return await service.update(tarea_id, data, user_id=current_user.user_id, roles=roles)


@router.delete(
    "/{tarea_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete tarea (admin/coord only)",
    dependencies=[Depends(require_permission(PERM_GESTIONAR))],
)
async def delete_tarea(
    tarea_id: UUID,
    service: Annotated[TareaService, Depends(_get_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    roles = await resolve_user_roles(db, current_user.user_id, current_user.tenant_id)
    await service.delete(tarea_id, user_id=current_user.user_id, roles=roles)


# ── Comentarios ────────────────────────────────────────────────────────

@router.post(
    "/{tarea_id}/comentarios",
    response_model=ComentarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add comment to tarea",
    dependencies=[Depends(require_permission(PERM_GESTIONAR))],
)
async def create_comentario(
    tarea_id: UUID,
    data: ComentarioCreate,
    service: Annotated[TareaService, Depends(_get_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    roles = await resolve_user_roles(db, current_user.user_id, current_user.tenant_id)
    return await service.agregar_comentario(
        tarea_id, data, user_id=current_user.user_id, roles=roles
    )


@router.get(
    "/{tarea_id}/comentarios",
    response_model=ComentarioListResponse,
    summary="List comments on a tarea",
    dependencies=[Depends(require_permission(PERM_GESTIONAR))],
)
async def list_comentarios(
    tarea_id: UUID,
    service: Annotated[TareaService, Depends(_get_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
):
    roles = await resolve_user_roles(db, current_user.user_id, current_user.tenant_id)
    items, total = await service.listar_comentarios(
        tarea_id, user_id=current_user.user_id, roles=roles, page=page, per_page=per_page
    )
    return ComentarioListResponse(items=items, total=total, page=page, per_page=per_page)
