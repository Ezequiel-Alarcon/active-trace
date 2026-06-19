"""Calificaciones API router (C-10).

Endpoints para importacion de calificaciones y consulta.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.core.dependencies import get_db
from app.core.permissions import require_permission
from app.domain.calificaciones.schemas.calificacion import (
    CalificacionConfirmRequest,
    CalificacionConfirmResponse,
    CalificacionCreate,
    CalificacionPreviewResponse,
    CalificacionRead,
)
from app.domain.calificaciones.services.calificacion_service import (
    CalificacionNotFoundError,
    CalificacionService,
)
from app.domain.calificaciones.services.import_service import (
    ImportService,
    ImportServiceError,
)
from app.models.usuario import Usuario
from app.repositories.usuarios import UsuarioRepository, decrypt_usuario_fields

router = APIRouter(prefix="/api/calificaciones", tags=["calificaciones"])


async def _get_calificacion_service(
    session: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> CalificacionService:
    return CalificacionService(session, current_user.tenant_id)


async def _get_import_service(
    session: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> tuple[ImportService, dict[str, UUID], set[UUID], set[UUID]]:
    usuario_repo = UsuarioRepository(session, current_user.tenant_id)
    usuarios = await usuario_repo.list(limit=10000)
    usuario_ids_by_email = {
        decrypt_usuario_fields(u)["email"].lower(): u.id for u in usuarios if u.email_enc
    }

    from app.models.materia import Materia
    from app.repositories.base import get_tenant_repository

    mat_repo = get_tenant_repository(Materia, session)
    materias = await mat_repo.list(limit=10000)
    materia_ids = {m.id for m in materias}

    from app.models.asignacion import Asignacion
    asig_repo = get_tenant_repository(Asignacion, session)
    asignaciones = await asig_repo.list(limit=10000)
    asignacion_ids = {a.id for a in asignaciones}

    svc = ImportService(
        session=session,
        tenant_id=current_user.tenant_id,
        usuario_ids_by_email=usuario_ids_by_email,
        materia_ids=materia_ids,
        asignacion_ids=asignacion_ids,
    )
    return svc, usuario_ids_by_email, materia_ids, asignacion_ids


@router.get("", response_model=list[CalificacionRead])
async def list_calificaciones(
    materia_id: Annotated[UUID | None, Query(description="Filtrar por materia")] = None,
    usuario_id: Annotated[UUID | None, Query(description="Filtrar por usuario")] = None,
    asignacion_id: Annotated[UUID | None, Query(description="Filtrar por asignacion")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    svc: CalificacionService = Depends(_get_calificacion_service),
    current_user: Usuario = Depends(get_current_user),
) -> list[CalificacionRead]:
    """Listar calificaciones con filtros opcionales."""
    require_permission("calificaciones:ver")
    return await svc.list_calificaciones(
        materia_id=materia_id,
        usuario_id=usuario_id,
        asignacion_id=asignacion_id,
        limit=limit,
        offset=offset,
    )


@router.post(
    "",
    response_model=CalificacionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_calificacion(
    data: CalificacionCreate,
    svc: CalificacionService = Depends(_get_calificacion_service),
    current_user: Usuario = Depends(get_current_user),
) -> CalificacionRead:
    """Crear una calificacion manual."""
    require_permission("calificaciones:importar")
    try:
        return await svc.create_calificacion(
            data=data.model_dump(),
            created_by=current_user.id,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/import/preview",
    response_model=CalificacionPreviewResponse,
    status_code=status.HTTP_200_OK,
)
async def import_preview(
    file: UploadFile = File(...),
    type: Annotated[str, Query(description="Tipo de import: 'grades' o 'completion'")] = "grades",
    svc_tuple: tuple[ImportService, dict[str, UUID], set[UUID], set[UUID]] = Depends(_get_import_service),
    current_user: Usuario = Depends(get_current_user),
) -> CalificacionPreviewResponse:
    """Parsear archivo de calificaciones y retornar preview sin persistir."""
    require_permission("calificaciones:importar")
    svc = svc_tuple[0]
    is_completion = type == "completion"
    content = await file.read()
    try:
        return svc.parse_preview(content, file.filename or "unknown", is_completion=is_completion)
    except ImportServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/import/confirm",
    response_model=CalificacionConfirmResponse,
    status_code=status.HTTP_200_OK,
)
async def import_confirm(
    data: CalificacionConfirmRequest,
    svc_tuple: tuple[ImportService, dict[str, UUID], set[UUID], set[UUID]] = Depends(_get_import_service),
    current_user: Usuario = Depends(get_current_user),
) -> CalificacionConfirmResponse:
    """Persistir las filas validas del preview token."""
    require_permission("calificaciones:importar")
    svc = svc_tuple[0]
    try:
        persisted, skipped, failed = await svc.confirm_import(
            preview_token=data.preview_token,
            created_by=current_user.user_id,
        )
        return CalificacionConfirmResponse(
            persisted=persisted,
            skipped=skipped,
            failed=failed,
        )
    except ImportServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{calificacion_id}",
    response_model=CalificacionRead,
)
async def get_calificacion(
    calificacion_id: UUID,
    svc: CalificacionService = Depends(_get_calificacion_service),
    current_user: Usuario = Depends(get_current_user),
) -> CalificacionRead:
    """Obtener una calificacion por ID."""
    require_permission("calificaciones:ver")
    try:
        return await svc.get_calificacion_by_id(calificacion_id)
    except CalificacionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
