"""Usuarios and Asignaciones router (C-07).

- /api/admin/usuarios  → guard usuarios:gestionar (ADMIN)
- /api/asignaciones    → guard equipos:asignar (COORDINADOR, ADMIN)
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_user
from app.core.dependencies import get_db
from app.core.permissions import require_permission
from app.schemas.usuarios import (
    AsignacionCreate,
    AsignacionResponse,
    AsignacionUpdate,
    UsuarioCreate,
    UsuarioResponse,
    UsuarioUpdate,
)
from app.services.usuarios import AsignacionService, UsuarioService

router = APIRouter(prefix="/api/admin", tags=["admin", "usuarios"])
asignacion_router = APIRouter(prefix="/api", tags=["asignaciones"])

PERM_USUARIOS = "usuarios:gestionar"
PERM_ASIGNACIONES = "equipos:asignar"


async def _get_usuario_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> UsuarioService:
    return UsuarioService(db, current_user.tenant_id)


async def _get_asignacion_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> AsignacionService:
    return AsignacionService(db, current_user.tenant_id)


# ── Usuarios ──────────────────────────────────────────────────────────

@router.get(
    "/usuarios",
    response_model=list[UsuarioResponse],
    summary="List usuarios",
    dependencies=[Depends(require_permission(PERM_USUARIOS))],
)
async def list_usuarios(
    request: Request,
    service: Annotated[UsuarioService, Depends(_get_usuario_service)],
    busqueda: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list:
    return await service.list(busqueda=busqueda, limit=limit, offset=offset)


@router.post(
    "/usuarios",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create usuario",
    dependencies=[Depends(require_permission(PERM_USUARIOS))],
)
async def create_usuario(
    request: Request,
    data: UsuarioCreate,
    service: Annotated[UsuarioService, Depends(_get_usuario_service)],
):
    return await service.create(data)


@router.get(
    "/usuarios/{usuario_id}",
    response_model=UsuarioResponse,
    summary="Get usuario by id",
    dependencies=[Depends(require_permission(PERM_USUARIOS))],
)
async def get_usuario(
    request: Request,
    usuario_id: UUID,
    service: Annotated[UsuarioService, Depends(_get_usuario_service)],
):
    return await service.get_by_id(usuario_id)


@router.patch(
    "/usuarios/{usuario_id}",
    response_model=UsuarioResponse,
    summary="Update usuario",
    dependencies=[Depends(require_permission(PERM_USUARIOS))],
)
async def update_usuario(
    request: Request,
    usuario_id: UUID,
    data: UsuarioUpdate,
    service: Annotated[UsuarioService, Depends(_get_usuario_service)],
):
    return await service.update(usuario_id, data)


@router.delete(
    "/usuarios/{usuario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Soft-delete usuario",
    dependencies=[Depends(require_permission(PERM_USUARIOS))],
)
async def delete_usuario(
    request: Request,
    usuario_id: UUID,
    service: Annotated[UsuarioService, Depends(_get_usuario_service)],
) -> None:
    await service.delete(usuario_id)


# ── Asignaciones ──────────────────────────────────────────────────────

@asignacion_router.get(
    "/asignaciones",
    response_model=list[AsignacionResponse],
    summary="List asignaciones",
    dependencies=[Depends(require_permission(PERM_ASIGNACIONES))],
)
async def list_asignaciones(
    request: Request,
    service: Annotated[AsignacionService, Depends(_get_asignacion_service)],
    usuario_id: UUID | None = None,
    rol_id: UUID | None = None,
    contexto_tipo: str | None = None,
    contexto_id: UUID | None = None,
    estado_vigencia: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list:
    return await service.list(
        usuario_id=usuario_id,
        rol_id=rol_id,
        contexto_tipo=contexto_tipo,
        contexto_id=contexto_id,
        estado_vigencia=estado_vigencia,
        limit=limit,
        offset=offset,
    )


@asignacion_router.post(
    "/asignaciones",
    response_model=AsignacionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create asignacion",
    dependencies=[Depends(require_permission(PERM_ASIGNACIONES))],
)
async def create_asignacion(
    request: Request,
    data: AsignacionCreate,
    service: Annotated[AsignacionService, Depends(_get_asignacion_service)],
):
    return await service.create(data)


@asignacion_router.get(
    "/asignaciones/{asignacion_id}",
    response_model=AsignacionResponse,
    summary="Get asignacion by id",
    dependencies=[Depends(require_permission(PERM_ASIGNACIONES))],
)
async def get_asignacion(
    request: Request,
    asignacion_id: UUID,
    service: Annotated[AsignacionService, Depends(_get_asignacion_service)],
):
    return await service.get_by_id(asignacion_id)


@asignacion_router.patch(
    "/asignaciones/{asignacion_id}",
    response_model=AsignacionResponse,
    summary="Update asignacion",
    dependencies=[Depends(require_permission(PERM_ASIGNACIONES))],
)
async def update_asignacion(
    request: Request,
    asignacion_id: UUID,
    data: AsignacionUpdate,
    service: Annotated[AsignacionService, Depends(_get_asignacion_service)],
):
    return await service.update(asignacion_id, data)


@asignacion_router.delete(
    "/asignaciones/{asignacion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Soft-delete asignacion",
    dependencies=[Depends(require_permission(PERM_ASIGNACIONES))],
)
async def delete_asignacion(
    request: Request,
    asignacion_id: UUID,
    service: Annotated[AsignacionService, Depends(_get_asignacion_service)],
) -> None:
    await service.delete(asignacion_id)
