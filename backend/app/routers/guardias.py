"""Guardias router (C-18 §7).

Endpoints for Guardia CRUD with role-based scope and CSV export.
TUTOR accesses own guardias via `encuentros:registrar_guardia`.
COORDINADOR/ADMIN access all via `encuentros:gestionar`.
"""

from __future__ import annotations

from typing import Annotated, Callable
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_user
from app.core.dependencies import get_db
from app.core.permissions import require_permission
from app.rbac.services import PermissionResolver
from app.models.usuario import Usuario
from app.schemas.guardias import (
    GuardiaCreate,
    GuardiaResponse,
    GuardiaUpdate,
)
from app.services.guardias import GuardiaService

router = APIRouter(prefix="/api/guardias", tags=["guardias"])

PERM_GUARDIA = "encuentros:registrar_guardia"
PERM_GESTIONAR = "encuentros:gestionar"


def require_any_permission(*permissions: str) -> Callable:
    """Factory: returns a FastAPI dependency that checks if the user holds
    ANY of the required permissions. Stores the full resolved set in
    request.state.permissions for downstream use."""

    async def _guard(
        request: Request,
        current_user: Annotated[CurrentUser, Depends(get_current_user)],
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> CurrentUser:
        resolver = PermissionResolver(db)
        resolved = await resolver.resolve(current_user.user_id, current_user.tenant_id)
        if not any(p in resolved for p in permissions):
            raise HTTPException(
                status_code=403,
                detail={"detail": f"No tiene ninguno de los permisos: {permissions}"},
            )
        request.state.permissions = resolved
        request.state.current_user = current_user
        return current_user

    return _guard


async def _get_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    request: Request,
) -> GuardiaService:
    permissions: set[str] = getattr(request.state, "permissions", set())
    return GuardiaService(db, current_user.tenant_id, current_user.user_id, permissions)


async def _resolve_tutor_nombre(db: AsyncSession, tenant_id: UUID, tutor_id: UUID) -> str:
    from sqlalchemy import select
    stmt = select(Usuario.nombre, Usuario.apellidos).where(
        Usuario.id == tutor_id,
        Usuario.tenant_id == tenant_id,
    )
    result = await db.execute(stmt)
    row = result.one_or_none()
    if row:
        return f"{row.nombre} {row.apellidos}"
    return ""


def _to_response(g, tutor_nombre: str | None = None) -> GuardiaResponse:
    return GuardiaResponse(
        id=g.id,
        tenant_id=g.tenant_id,
        tutor_id=g.tutor_id,
        tutor_nombre=tutor_nombre,
        materia_id=g.materia_id,
        cohorte_id=g.cohorte_id,
        fecha=g.fecha,
        hora_inicio=g.hora_inicio,
        hora_fin=g.hora_fin,
        titulo=g.titulo,
        observaciones=g.observaciones,
        created_at=g.created_at,
        updated_at=g.updated_at,
    )


# ── Guardias CRUD ─────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=list[GuardiaResponse],
    summary="List guardias",
    dependencies=[Depends(require_any_permission(PERM_GUARDIA, PERM_GESTIONAR))],
)
async def list_guardias(
    request: Request,
    service: Annotated[GuardiaService, Depends(_get_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
    materia_id: UUID | None = Query(None),
    cohorte_id: UUID | None = Query(None),
    fecha_desde: str | None = Query(None),
    fecha_hasta: str | None = Query(None),
) -> list:
    from datetime import date
    fd = date.fromisoformat(fecha_desde) if fecha_desde else None
    fh = date.fromisoformat(fecha_hasta) if fecha_hasta else None
    guardias = await service.list_guardias(
        materia_id=materia_id,
        cohorte_id=cohorte_id,
        fecha_desde=fd,
        fecha_hasta=fh,
    )
    tenant_id = service._tenant_id
    result = []
    for g in guardias:
        nombre = await _resolve_tutor_nombre(db, tenant_id, g.tutor_id)
        result.append(_to_response(g, nombre))
    return result


@router.post(
    "/",
    response_model=GuardiaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register guardia",
    dependencies=[Depends(require_permission(PERM_GUARDIA))],
)
async def create_guardia(
    request: Request,
    data: GuardiaCreate,
    service: Annotated[GuardiaService, Depends(_get_service)],
):
    g = await service.create_guardia(data)
    return _to_response(g)


@router.get(
    "/{guardia_id}",
    response_model=GuardiaResponse,
    summary="Get guardia by id",
    dependencies=[Depends(require_permission(PERM_GUARDIA))],
)
async def get_guardia(
    request: Request,
    guardia_id: UUID,
    service: Annotated[GuardiaService, Depends(_get_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    g = await service.get_guardia(guardia_id)
    nombre = await _resolve_tutor_nombre(db, service._tenant_id, g.tutor_id)
    return _to_response(g, nombre)


@router.patch(
    "/{guardia_id}",
    response_model=GuardiaResponse,
    summary="Update guardia",
    dependencies=[Depends(require_permission(PERM_GUARDIA))],
)
async def update_guardia(
    request: Request,
    guardia_id: UUID,
    data: GuardiaUpdate,
    service: Annotated[GuardiaService, Depends(_get_service)],
):
    g = await service.update_guardia(guardia_id, data)
    return _to_response(g)


@router.delete(
    "/{guardia_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Soft-delete guardia",
    dependencies=[Depends(require_permission(PERM_GUARDIA))],
)
async def delete_guardia(
    request: Request,
    guardia_id: UUID,
    service: Annotated[GuardiaService, Depends(_get_service)],
) -> None:
    await service.delete_guardia(guardia_id)


# ── Export CSV ────────────────────────────────────────────────────────

@router.get(
    "/export",
    response_class=StreamingResponse,
    summary="Export guardias to CSV",
    dependencies=[Depends(require_permission(PERM_GESTIONAR))],
)
async def export_guardias_csv(
    request: Request,
    service: Annotated[GuardiaService, Depends(_get_service)],
    materia_id: UUID | None = Query(None),
    cohorte_id: UUID | None = Query(None),
    fecha_desde: str | None = Query(None),
    fecha_hasta: str | None = Query(None),
):
    from datetime import date
    fd = date.fromisoformat(fecha_desde) if fecha_desde else None
    fh = date.fromisoformat(fecha_hasta) if fecha_hasta else None
    csv_content = await service.export_guardias_csv(
        materia_id=materia_id,
        cohorte_id=cohorte_id,
        fecha_desde=fd,
        fecha_hasta=fh,
    )
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=guardias.csv"},
    )
