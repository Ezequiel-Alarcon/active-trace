"""Impersonation management router (C-05 §9)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_user
from app.audit.constants import (
    AUDIT_IMPERSONACION_FINALIZAR,
    AUDIT_IMPERSONACION_INICIAR,
)
from app.audit.impersonation import (
    end_impersonation,
    get_impersonated_user_id,
    get_impersonation_record,
    is_impersonating,
    start_impersonation,
)
from app.audit.repositories import AuditLogRepository
from app.core.dependencies import get_db
from app.core.permissions import require_permission

router = APIRouter(prefix="/api/impersonation", tags=["impersonation"])


class ImpersonationStartRequest(BaseModel):
    """Request body to start impersonation."""

    model_config = ConfigDict(extra="forbid")

    target_user_id: UUID


class ImpersonationStartResponse(BaseModel):
    """Response after starting impersonation."""

    model_config = ConfigDict(extra="forbid")

    message: str
    impersonated_user_id: UUID


@router.post(
    "/start",
    response_model=ImpersonationStartResponse,
    status_code=status.HTTP_200_OK,
    summary="Start impersonation session",
    dependencies=[Depends(require_permission("impersonacion:usar"))],
)
async def impersonation_start(
    request: Request,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    data: ImpersonationStartRequest,
) -> ImpersonationStartResponse:
    """Start an impersonation session.

    The current user (admin) will impersonate the target user.
    Writes an IMPERSONACION_INICIAR audit entry.
    """
    actor_id = current_user.user_id
    target_user_id = data.target_user_id

    if is_impersonating(actor_id):
        existing_target = get_impersonated_user_id(actor_id)
        if existing_target == target_user_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"detail": "Ya esta impersonando a ese usuario"},
            )
        end_impersonation(actor_id)

    start_impersonation(actor_id, target_user_id)

    ip = getattr(request.state, "ip", "0.0.0.0")
    user_agent = getattr(request.state, "user_agent", "unknown")

    repo = AuditLogRepository(db, current_user.tenant_id)
    await repo.create(
        actor_id=actor_id,
        accion=AUDIT_IMPERSONACION_INICIAR,
        impersonado_id=target_user_id,
        detalle={"target_user_id": str(target_user_id)},
        filas_afectadas=0,
        ip=str(ip),
        user_agent=str(user_agent),
    )
    await db.commit()

    return ImpersonationStartResponse(
        message="Impersonacion iniciada",
        impersonated_user_id=target_user_id,
    )


@router.delete(
    "/end",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="End impersonation session",
    dependencies=[Depends(require_permission("impersonacion:usar"))],
)
async def impersonation_end(
    request: Request,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """End the current impersonation session.

    Writes an IMPERSONACION_FINALIZAR audit entry.
    """
    actor_id = current_user.user_id

    if not is_impersonating(actor_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"detail": "No hay una sesion de impersonacion activa"},
        )

    record = get_impersonation_record(actor_id)
    target_user_id = record.target_user_id if record else None

    ended = end_impersonation(actor_id)
    if not ended:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"detail": "No se pudo finalizar la impersonacion"},
        )

    ip = getattr(request.state, "ip", "0.0.0.0")
    user_agent = getattr(request.state, "user_agent", "unknown")

    repo = AuditLogRepository(db, current_user.tenant_id)
    await repo.create(
        actor_id=actor_id,
        accion=AUDIT_IMPERSONACION_FINALIZAR,
        impersonado_id=target_user_id,
        detalle={"target_user_id": str(target_user_id) if target_user_id else None},
        filas_afectadas=0,
        ip=str(ip),
        user_agent=str(user_agent),
    )
    await db.commit()