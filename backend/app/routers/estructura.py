"""Estructura academica router (C-06 §4).

All endpoints require estructura:gestionar permission.
Mounted at /api/admin in app/api/v1/main_router.py.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_user
from app.core.dependencies import get_db
from app.core.permissions import require_permission
from app.schemas.estructura import (
    CarreraCreate,
    CarreraResponse,
    CarreraUpdate,
    CohorteCreate,
    CohorteResponse,
    CohorteUpdate,
    MateriaCreate,
    MateriaResponse,
    MateriaUpdate,
)
from app.services.estructura import EstructuraService

router = APIRouter(prefix="/api/admin", tags=["admin", "estructura"])

PERM = "estructura:gestionar"


async def _get_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> EstructuraService:
    return EstructuraService(db, current_user.tenant_id)


# ── Carreras ──────────────────────────────────────────────────────────

@router.get(
    "/carreras",
    response_model=list[CarreraResponse],
    summary="List carreras",
    dependencies=[Depends(require_permission(PERM))],
)
async def list_carreras(
    request: Request,
    service: Annotated[EstructuraService, Depends(_get_service)],
    estado: str | None = None,
) -> list:
    return await service.list_carreras(estado=estado)


@router.post(
    "/carreras",
    response_model=CarreraResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create carrera",
    dependencies=[Depends(require_permission(PERM))],
)
async def create_carrera(
    request: Request,
    data: CarreraCreate,
    service: Annotated[EstructuraService, Depends(_get_service)],
):
    return await service.create_carrera(data)


@router.get(
    "/carreras/{carrera_id}",
    response_model=CarreraResponse,
    summary="Get carrera by id",
    dependencies=[Depends(require_permission(PERM))],
)
async def get_carrera(
    request: Request,
    carrera_id: UUID,
    service: Annotated[EstructuraService, Depends(_get_service)],
):
    return await service.get_carrera(carrera_id)


@router.patch(
    "/carreras/{carrera_id}",
    response_model=CarreraResponse,
    summary="Update carrera",
    dependencies=[Depends(require_permission(PERM))],
)
async def update_carrera(
    request: Request,
    carrera_id: UUID,
    data: CarreraUpdate,
    service: Annotated[EstructuraService, Depends(_get_service)],
):
    return await service.update_carrera(carrera_id, data)


@router.delete(
    "/carreras/{carrera_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Soft-delete carrera",
    dependencies=[Depends(require_permission(PERM))],
)
async def delete_carrera(
    request: Request,
    carrera_id: UUID,
    service: Annotated[EstructuraService, Depends(_get_service)],
) -> None:
    await service.delete_carrera(carrera_id)


# ── Cohortes ─────────────────────────────────────────────────────────

@router.get(
    "/cohortes",
    response_model=list[CohorteResponse],
    summary="List cohortes",
    dependencies=[Depends(require_permission(PERM))],
)
async def list_cohortes(
    request: Request,
    service: Annotated[EstructuraService, Depends(_get_service)],
    carrera_id: UUID | None = None,
    estado: str | None = None,
) -> list:
    return await service.list_cohortes(carrera_id=carrera_id, estado=estado)


@router.post(
    "/cohortes",
    response_model=CohorteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create cohorte",
    dependencies=[Depends(require_permission(PERM))],
)
async def create_cohorte(
    request: Request,
    data: CohorteCreate,
    service: Annotated[EstructuraService, Depends(_get_service)],
):
    return await service.create_cohorte(data)


@router.get(
    "/cohortes/{cohorte_id}",
    response_model=CohorteResponse,
    summary="Get cohorte by id",
    dependencies=[Depends(require_permission(PERM))],
)
async def get_cohorte(
    request: Request,
    cohorte_id: UUID,
    service: Annotated[EstructuraService, Depends(_get_service)],
):
    return await service.get_cohorte(cohorte_id)


@router.patch(
    "/cohortes/{cohorte_id}",
    response_model=CohorteResponse,
    summary="Update cohorte",
    dependencies=[Depends(require_permission(PERM))],
)
async def update_cohorte(
    request: Request,
    cohorte_id: UUID,
    data: CohorteUpdate,
    service: Annotated[EstructuraService, Depends(_get_service)],
):
    return await service.update_cohorte(cohorte_id, data)


@router.delete(
    "/cohortes/{cohorte_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Soft-delete cohorte",
    dependencies=[Depends(require_permission(PERM))],
)
async def delete_cohorte(
    request: Request,
    cohorte_id: UUID,
    service: Annotated[EstructuraService, Depends(_get_service)],
) -> None:
    await service.delete_cohorte(cohorte_id)


# ── Materias ─────────────────────────────────────────────────────────

@router.get(
    "/materias",
    response_model=list[MateriaResponse],
    summary="List materias",
    dependencies=[Depends(require_permission(PERM))],
)
async def list_materias(
    request: Request,
    service: Annotated[EstructuraService, Depends(_get_service)],
    estado: str | None = None,
) -> list:
    return await service.list_materias(estado=estado)


@router.post(
    "/materias",
    response_model=MateriaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create materia",
    dependencies=[Depends(require_permission(PERM))],
)
async def create_materia(
    request: Request,
    data: MateriaCreate,
    service: Annotated[EstructuraService, Depends(_get_service)],
):
    return await service.create_materia(data)


@router.get(
    "/materias/{materia_id}",
    response_model=MateriaResponse,
    summary="Get materia by id",
    dependencies=[Depends(require_permission(PERM))],
)
async def get_materia(
    request: Request,
    materia_id: UUID,
    service: Annotated[EstructuraService, Depends(_get_service)],
):
    return await service.get_materia(materia_id)


@router.patch(
    "/materias/{materia_id}",
    response_model=MateriaResponse,
    summary="Update materia",
    dependencies=[Depends(require_permission(PERM))],
)
async def update_materia(
    request: Request,
    materia_id: UUID,
    data: MateriaUpdate,
    service: Annotated[EstructuraService, Depends(_get_service)],
):
    return await service.update_materia(materia_id, data)


@router.delete(
    "/materias/{materia_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Soft-delete materia",
    dependencies=[Depends(require_permission(PERM))],
)
async def delete_materia(
    request: Request,
    materia_id: UUID,
    service: Annotated[EstructuraService, Depends(_get_service)],
) -> None:
    await service.delete_materia(materia_id)
