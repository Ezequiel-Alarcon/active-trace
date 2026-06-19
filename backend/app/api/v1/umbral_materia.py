"""UmbralMateria API router (C-10).

Endpoints para CRUD de umbrales de aprobacion.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.core.dependencies import get_db
from app.core.permissions import require_permission
from app.domain.calificaciones.schemas.umbral_materia import (
    UmbralMateriaCreate,
    UmbralMateriaRead,
    UmbralMateriaUpdate,
)
from app.domain.calificaciones.services.umbral_service import (
    UmbralDuplicateError,
    UmbralNotFoundError,
    UmbralService,
)
from app.models.usuario import Usuario

router = APIRouter(prefix="/api/umbral-materia", tags=["umbral-materia"])


async def _get_umbral_service(
    session: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> UmbralService:
    return UmbralService(session, current_user.tenant_id)


@router.get("", response_model=list[UmbralMateriaRead], dependencies=[Depends(require_permission("calificaciones:ver"))])
async def list_umbrales(
    materia_id: Annotated[UUID | None, Query(description="Filtrar por materia")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    svc: UmbralService = Depends(_get_umbral_service),
    current_user: Usuario = Depends(get_current_user),
) -> list[UmbralMateriaRead]:
    """Listar umbrales con filtro opcional por materia."""
    return await svc.list_umbrales(materia_id=materia_id, limit=limit, offset=offset)


@router.post(
    "",
    response_model=UmbralMateriaRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("calificaciones:importar"))],
)
async def create_umbral(
    data: UmbralMateriaCreate,
    svc: UmbralService = Depends(_get_umbral_service),
    current_user: Usuario = Depends(get_current_user),
) -> UmbralMateriaRead:
    """Crear un nuevo umbral para materia/asignacion."""
    try:
        return await svc.create_umbral(data.model_dump())
    except UmbralDuplicateError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un umbral para esta materia y asignación",
        )


@router.put(
    "/{umbral_id}",
    response_model=UmbralMateriaRead,
    dependencies=[Depends(require_permission("calificaciones:importar"))],
)
async def update_umbral(
    umbral_id: UUID,
    data: UmbralMateriaUpdate,
    svc: UmbralService = Depends(_get_umbral_service),
    current_user: Usuario = Depends(get_current_user),
) -> UmbralMateriaRead:
    """Actualizar un umbral existente."""
    try:
        return await svc.update_umbral(umbral_id, data)
    except UmbralNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))