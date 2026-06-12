"""Padron router (C-09).

Endpoints para ingestión de padrón de alumnos desde archivos xlsx/csv
y sincronización con Moodle Web Services.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.core.dependencies import get_db
from app.core.permissions import require_permission
from app.integrations.moodle_ws import MoodleWSClient, MoodleWSError
from app.models.usuario import Usuario
from app.repositories.padron import PadronRepository
from app.repositories.usuarios import UsuarioRepository
from app.schemas.padron import (
    PadronPreviewResponse,
    VersionPadronCreate,
    VersionPadronResponse,
)
from app.services.padron import (
    DangerousExtensionError,
    FileTooLargeError,
    PadronService,
    PadronServiceError,
)

router = APIRouter(prefix="/api/padrones", tags=["padrones"])


async def _get_padron_service(
    session: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> PadronService:
    return PadronService(session, current_user.tenant_id)


async def _get_usuario_ids_by_email(
    session: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> dict[str, UUID]:
    """Build a dict mapping lowercase email -> usuario_id for the current tenant."""
    repo = UsuarioRepository(session, current_user.tenant_id)
    usuarios = await repo.list_all()
    return {u.email.lower(): u.id for u in usuarios if u.email}


@router.post(
    "/preview",
    response_model=PadronPreviewResponse,
    status_code=status.HTTP_200_OK,
)
async def preview_padron(
    file: UploadFile = File(...),
    svc: PadronService = Depends(_get_padron_service),
    usuario_ids_by_email: dict[str, UUID] = Depends(_get_usuario_ids_by_email),
) -> PadronPreviewResponse:
    """Parse uploaded xlsx/csv and return preview rows without persisting."""
    require_permission("padron:importar")

    content = await file.read()
    try:
        return await svc.preview(content, file.filename or "unknown", usuario_ids_by_email)
    except PadronServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "",
    response_model=VersionPadronResponse,
    status_code=status.HTTP_201_CREATED,
)
async def import_padron(
    data: VersionPadronCreate,
    svc: PadronService = Depends(_get_padron_service),
    current_user: Usuario = Depends(get_current_user),
) -> VersionPadronResponse:
    """Persist a new padron version with its entries. Requires prior preview."""
    require_permission("padron:importar")

    try:
        version = await svc.import_padron(data, current_user.id)
        return VersionPadronResponse(
            id=version.id,
            tenant_id=version.tenant_id,
            materia_id=version.materia_id,
            cohorte_id=version.cohorte_id,
            cargado_por=version.cargado_por,
            cargado_at=version.cargado_at,
            activa=version.activa,
            created_at=version.created_at,
            updated_at=version.updated_at,
        )
    except PadronServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/materia/{materia_id}/cohorte/{cohorte_id}",
    response_model=list[VersionPadronResponse],
)
async def list_padrones(
    materia_id: UUID,
    cohorte_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> list[VersionPadronResponse]:
    """List all padron versions for a materia-cohorte pair."""
    require_permission("padron:ver")

    repo = PadronRepository(session, current_user.tenant_id)
    versions = await repo.list_by_materia_cohorte(materia_id, cohorte_id)
    return [
        VersionPadronResponse(
            id=v.id,
            tenant_id=v.tenant_id,
            materia_id=v.materia_id,
            cohorte_id=v.cohorte_id,
            cargado_por=v.cargado_por,
            cargado_at=v.cargado_at,
            activa=v.activa,
            created_at=v.created_at,
            updated_at=v.updated_at,
        )
        for v in versions
    ]


@router.get(
    "/{version_id}/entradas",
    response_model=list[dict[str, Any]],
)
async def list_entradas(
    version_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """List all entries for a padron version."""
    require_permission("padron:ver")

    repo = PadronRepository(session, current_user.tenant_id)
    version = await repo.get_version_by_id(version_id)
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Versión no encontrada")

    entradas = await repo.get_entries_by_version(version_id)
    return [
        {
            "id": str(e.id),
            "nombre": e.nombre,
            "apellidos": e.apellidos,
            "email": e.email,
            "comision": e.comision,
            "regional": e.regional,
            "usuario_id": str(e.usuario_id) if e.usuario_id else None,
        }
        for e in entradas
    ]


@router.patch(
    "/{version_id}/activar",
    response_model=VersionPadronResponse,
)
async def activar_version(
    version_id: UUID,
    svc: PadronService = Depends(_get_padron_service),
) -> VersionPadronResponse:
    """Activate a specific padron version, deactivating all others for the same materia-cohorte."""
    require_permission("padron:importar")

    try:
        version = await svc.activar_version(version_id)
        return VersionPadronResponse(
            id=version.id,
            tenant_id=version.tenant_id,
            materia_id=version.materia_id,
            cohorte_id=version.cohorte_id,
            cargado_por=version.cargado_por,
            cargado_at=version.cargado_at,
            activa=version.activa,
            created_at=version.created_at,
            updated_at=version.updated_at,
        )
    except PadronServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/materia/{materia_id}/cohorte/{cohorte_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def vaciar_datos(
    materia_id: UUID,
    cohorte_id: UUID,
    svc: PadronService = Depends(_get_padron_service),
    current_user: Usuario = Depends(get_current_user),
) -> None:
    """Vaciar todos los datos de padrón de una materia-cohorte (soft-delete)."""
    require_permission("padron:importar")

    try:
        await svc.vaciar_datos(materia_id, cohorte_id, current_user.id)
    except PadronServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/moodle/sync/{materia_id}/{cohorte_id}")
async def sync_from_moodle(
    materia_id: UUID,
    cohorte_id: UUID,
    current_user: Usuario = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Sincronizar padrón desde Moodle WS. Si falla, devuelve 502 con sugerencia de import manual."""
    require_permission("padron:importar")

    from app.core.config import settings

    moodle_url = getattr(settings, "moodle_ws_url", None)
    moodle_token = getattr(settings, "moodle_ws_token", None)

    if not moodle_url or not moodle_token:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Moodle WS no configurado. Use importación manual con archivo xlsx/csv.",
        )

    client = MoodleWSClient(base_url=moodle_url, token=moodle_token)

    try:
        # TODO: obtener course_id de la materia (requiere integración con Moodle)
        # Por ahora devolvemos que la feature está en construcción
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="La sincronización con Moodle requiere mapeo materia→course_id. Use importación manual.",
        )
    except MoodleWSError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error de Moodle: {e}. Use importación manual con archivo xlsx/csv.",
        ) from e
    finally:
        await client.close()