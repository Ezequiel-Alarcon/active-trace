"""Comisiones API router."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_user
from app.core.dependencies import get_db
from app.core.permissions import require_permission
from app.domain.comisiones.service import ComisionesService
from app.schemas.comisiones import ComisionRead

router = APIRouter(prefix="/api/comisiones", tags=["comisiones"])


def _get_service(
    session: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> ComisionesService:
    return ComisionesService(session, current_user.tenant_id)


@router.get("", response_model=list[ComisionRead])
async def list_comisiones(
    svc: ComisionesService = Depends(_get_service),
    _authorized: CurrentUser = Depends(require_permission("analisis:ver")),
) -> list[ComisionRead]:
    return await svc.list_active()
