from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

# TODO: (FEAT) Agregar permiso perfil:ver al catálogo y decorar estos
# endpoints con require_permission para mantener consistencia.
# TODO: (REVIEW) Auditoría backend/frontend 2026-06-19: la pantalla de perfil
# funciona solo por autenticación, no por RBAC explícito. Para un proyecto
# fail-closed esto queda incompleto: no existe `perfil:ver`/`perfil:editar` en
# migraciones ni guards en router.
# TODO: (REVIEW) Auditoría backend/frontend 2026-06-19: el contrato real es
# `/api/perfil/` para GET/PATCH. Si el frontend nuevo espera `/api/auth/me` o
# `/api/usuarios/me`, hay desalineación de rutas aunque la funcionalidad exista.
from app.auth.deps import CurrentUser, get_current_user
from app.core.dependencies import get_db
from app.schemas.perfil import PerfilResponse, PerfilUpdate
from app.services.perfil import PerfilService

router = APIRouter(prefix="/api/perfil", tags=["perfil"])


def _get_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> PerfilService:
    return PerfilService(db, current_user.tenant_id)


@router.get(
    "/",
    response_model=PerfilResponse,
    summary="Get own profile",
)
async def get_perfil(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[PerfilService, Depends(_get_service)],
):
    return await service.get_profile(current_user.user_id)


@router.patch(
    "/",
    response_model=PerfilResponse,
    summary="Update own profile",
)
async def update_perfil(
    data: PerfilUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[PerfilService, Depends(_get_service)],
):
    return await service.update_profile(current_user.user_id, data)
