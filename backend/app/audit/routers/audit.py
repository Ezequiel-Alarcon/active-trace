"""Audit log read router (C-05 §9)."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_user
from app.audit.models import AuditLog
from app.audit.schemas import AuditLogPageResponse, AuditLogResponse
from app.audit.services import AuditLogService
from app.core.dependencies import get_db
from app.core.permissions import require_permission

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get(
    "/log",
    response_model=AuditLogPageResponse,
    summary="List audit log entries",
    dependencies=[Depends(require_permission("auditoria:ver"))],
)
async def list_audit_logs(
    request: Request,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    actor: Annotated[UUID | None, Query(alias="actor")] = None,
    accion: Annotated[str | None, Query(alias="accion")] = None,
    from_date: Annotated[datetime | None, Query(alias="from")] = None,
    to_date: Annotated[datetime | None, Query(alias="to")] = None,
    impersonado: Annotated[UUID | None, Query(alias="impersonado")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
    all_tenants: Annotated[bool, Query(alias="all_tenants")] = False,
) -> AuditLogPageResponse:
    """List audit log entries with optional filters.

    Requires `auditoria:ver` permission.
    The `all_tenants` flag is only permitted for users with `auditoria:ver_todos`
    permission (admin-level).
    """
    is_admin = False
    if all_tenants:
        permissions: set[str] = getattr(request.state, "permissions", set())
        if "auditoria:ver_todos" not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"detail": "No tiene permiso para ver logs de todos los tenants"},
            )
        is_admin = True

    service = AuditLogService(db, current_user.tenant_id)

    items, total = await service.get_logs(
        tenant_id=current_user.tenant_id,
        actor_id=actor,
        accion=accion,
        from_date=from_date,
        to_date=to_date,
        impersonado_id=impersonado,
        page=page,
        page_size=page_size,
        is_admin=is_admin,
    )

    return AuditLogPageResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[
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
        ],
    )