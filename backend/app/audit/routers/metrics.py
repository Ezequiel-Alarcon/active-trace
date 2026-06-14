"""Audit metrics router — panel de auditoría (C-19).

Read-only aggregation endpoints over AuditLog. All endpoints require
`auditoria:ver`. Users with only `ver` (COORDINADOR scope) are filtered
to their assigned materias. ADMIN/FINANZAS with `ver_todos` see all.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_user
from app.audit.schemas import (
    ActionsPerDayResponse,
    AuditLogResponse,
    ComunicacionStatusItem,
    InteractionItem,
)
from app.audit.services import AuditLogService
from app.core.dependencies import get_db
from app.core.permissions import require_permission

router = APIRouter(prefix="/api/audit/metrics", tags=["audit"])
METRICS_PERM = require_permission("auditoria:ver")


async def _resolve_materia_ids(
    request: Request,
    service: AuditLogService,
    current_user: CurrentUser,
) -> list[UUID] | None:
    """Return materia_ids filter or None if user sees all."""
    permissions: set[str] = getattr(request.state, "permissions", set())
    if "auditoria:ver_todos" in permissions:
        return None
    materia_ids = await service._resolve_scope_materias(current_user.user_id)
    return materia_ids if materia_ids else None


async def _get_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> AuditLogService:
    return AuditLogService(db, current_user.tenant_id)


@router.get(
    "/actions-per-day",
    response_model=list[ActionsPerDayResponse],
    summary="Actions grouped by day",
    dependencies=[Depends(METRICS_PERM)],
)
async def actions_per_day(
    request: Request,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[AuditLogService, Depends(_get_service)],
    actor_id: Annotated[UUID | None, Query(description="Filter by actor")] = None,
    from_date: Annotated[datetime | None, Query(alias="from")] = None,
    to_date: Annotated[datetime | None, Query(alias="to")] = None,
) -> list[ActionsPerDayResponse]:
    materia_ids = await _resolve_materia_ids(request, service, current_user)
    result = await service.get_actions_per_day(
        actor_id=actor_id,
        from_date=from_date,
        to_date=to_date,
        materia_ids=materia_ids,
    )
    return [ActionsPerDayResponse(**row) for row in result]


@router.get(
    "/comunicacion-status",
    response_model=list[ComunicacionStatusItem],
    summary="Communication status by materia and docente",
    dependencies=[Depends(METRICS_PERM)],
)
async def comunicacion_status(
    request: Request,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[AuditLogService, Depends(_get_service)],
) -> list[ComunicacionStatusItem]:
    materia_ids = await _resolve_materia_ids(request, service, current_user)
    result = await service.get_comunicacion_status(materia_ids=materia_ids)
    return [ComunicacionStatusItem(**row) for row in result]


@router.get(
    "/interactions",
    response_model=list[InteractionItem],
    summary="Interaction counts by materia, docente, and action",
    dependencies=[Depends(METRICS_PERM)],
)
async def interactions_summary(
    request: Request,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[AuditLogService, Depends(_get_service)],
) -> list[InteractionItem]:
    materia_ids = await _resolve_materia_ids(request, service, current_user)
    result = await service.get_interactions_summary(materia_ids=materia_ids)
    return [InteractionItem(**row) for row in result]


@router.get(
    "/last-actions",
    response_model=list[AuditLogResponse],
    summary="Last N audit entries",
    dependencies=[Depends(METRICS_PERM)],
)
async def last_actions(
    request: Request,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[AuditLogService, Depends(_get_service)],
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
) -> list[AuditLogResponse]:
    materia_ids = await _resolve_materia_ids(request, service, current_user)
    items = await service.get_last_actions(limit=limit, materia_ids=materia_ids)
    return [
        AuditLogResponse(
            id=item.id,
            tenant_id=item.tenant_id,
            fecha_hora=item.fecha_hora,
            actor_id=item.actor_id,
            impersonado_id=item.impersonado_id,
            materia_id=item.materia_id,
            accion=item.accion,
            detalle=item.detalle,
            filas_afectadas=item.filas_afectadas,
            ip=item.ip,
            user_agent=item.user_agent,
        )
        for item in items
    ]
