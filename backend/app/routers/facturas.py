from __future__ import annotations

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_user
from app.core.dependencies import get_db
from app.core.permissions import require_permission
from app.schemas.liquidaciones import (
    FacturaCreate,
    FacturaDescargaResponse,
    FacturaPagoConfirm,
    FacturaResponse,
)
from app.services.liquidaciones import FacturaService

router = APIRouter(prefix="/api/facturas", tags=["facturas"])


async def _service(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> FacturaService:
    return FacturaService(db, current_user.tenant_id)


@router.post("", response_model=FacturaResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("facturas:gestionar"))])
async def registrar(
    data: FacturaCreate,
    service: Annotated[FacturaService, Depends(_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    return await service.registrar(data, actor_id=current_user.user_id)


@router.get("", response_model=list[FacturaResponse], dependencies=[Depends(require_permission("facturas:ver"))])
async def listar(
    service: Annotated[FacturaService, Depends(_service)],
    estado: str | None = None,
    usuario_id: UUID | None = None,
    desde: date | None = None,
    hasta: date | None = None,
):
    return await service.listar(estado=estado, usuario_id=usuario_id, desde=desde, hasta=hasta)


@router.post("/{factura_id}/abonada", response_model=FacturaResponse, dependencies=[Depends(require_permission("facturas:gestionar"))])
async def marcar_abonada(
    factura_id: UUID,
    data: FacturaPagoConfirm,
    service: Annotated[FacturaService, Depends(_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    return await service.marcar_abonada(factura_id, data, actor_id=current_user.user_id)


@router.get("/{factura_id}/descarga", response_model=FacturaDescargaResponse, dependencies=[Depends(require_permission("facturas:descargar"))])
async def descargar(factura_id: UUID, service: Annotated[FacturaService, Depends(_service)]):
    return await service.resolver_descarga(factura_id)
