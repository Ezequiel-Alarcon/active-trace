from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_user
from app.core.dependencies import get_db
from app.core.permissions import require_permission
from app.schemas.liquidaciones import (
    LiquidacionCalcularRequest,
    LiquidacionCerrarRequest,
    LiquidacionCierreResponse,
    LiquidacionItem,
    LiquidacionResultado,
    SalarioBaseCreate,
    SalarioPlusCreate,
    SalarioResponse,
    SalarioPlusResponse,
)
from app.services.liquidaciones import GrillaSalarialService, LiquidacionService

router = APIRouter(prefix="/api/liquidaciones", tags=["liquidaciones"])


async def _liquidacion_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> LiquidacionService:
    return LiquidacionService(db, current_user.tenant_id)


async def _grilla_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> GrillaSalarialService:
    return GrillaSalarialService(db, current_user.tenant_id)


@router.post("/salarios/base", response_model=SalarioResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("liquidaciones:configurar-salarios"))])
async def create_salario_base(data: SalarioBaseCreate, service: Annotated[GrillaSalarialService, Depends(_grilla_service)]):
    return await service.create_salario_base(data)


@router.post("/salarios/plus", response_model=SalarioPlusResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("liquidaciones:configurar-salarios"))])
async def create_salario_plus(data: SalarioPlusCreate, service: Annotated[GrillaSalarialService, Depends(_grilla_service)]):
    return await service.create_salario_plus(data)


@router.post("/calcular", response_model=LiquidacionResultado, dependencies=[Depends(require_permission("liquidaciones:calcular"))])
async def calcular(data: LiquidacionCalcularRequest, service: Annotated[LiquidacionService, Depends(_liquidacion_service)]):
    return await service.calcular(data)


@router.post("/cerrar", response_model=LiquidacionCierreResponse, dependencies=[Depends(require_permission("liquidaciones:cerrar"))])
async def cerrar(
    data: LiquidacionCerrarRequest,
    service: Annotated[LiquidacionService, Depends(_liquidacion_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    return await service.cerrar(data, actor_id=current_user.user_id)


@router.get("/historial", response_model=list[LiquidacionItem], dependencies=[Depends(require_permission("liquidaciones:ver"))])
async def historial(service: Annotated[LiquidacionService, Depends(_liquidacion_service)], usuario_id: UUID | None = None):
    return await service.historial(usuario_id)


@router.get("/exportar", response_model=LiquidacionResultado, dependencies=[Depends(require_permission("liquidaciones:exportar"))])
async def exportar(service: Annotated[LiquidacionService, Depends(_liquidacion_service)], cohorte_id: UUID, periodo: str):
    return await service.exportar(cohorte_id, periodo)
