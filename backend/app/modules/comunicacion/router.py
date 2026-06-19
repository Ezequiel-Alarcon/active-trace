"""Comunicacion API router — enqueue, preview, approve/reject lotes."""

from __future__ import annotations

import time
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.audit.constants import AUDIT_COMUNICACION_APROBAR, AUDIT_COMUNICACION_ENVIAR
from app.core.audit import audit_emit
from app.core.dependencies import get_db
from app.core.permissions import require_permission
from app.models.usuario import Usuario
from app.modules.comunicacion.models.comunicacion import (
    Comunicacion,
    ComunicacionEstado,
)
from app.modules.comunicacion.repositories.comunicacion import ComunicacionRepository
from app.modules.comunicacion.schemas.comunicacion import (
    ComunicacionCreate,
    ComunicacionResponse,
    LoteStatusResponse,
)
from app.modules.comunicacion.schemas.lote import LoteAprobarRequest, LoteRechazarRequest
from app.modules.comunicacion.schemas.preview import PreviewRequest, PreviewResponse
from app.modules.comunicacion.services.approval import ApprovalService
from app.modules.comunicacion.services.preview import PreviewService

router = APIRouter(prefix="/api/comunicaciones", tags=["comunicaciones"])

# In-memory preview tracking (RN-16: preview-before-send).
# Maps user_id string → timestamp of last /preview call.
_user_preview_at: dict[str, float] = {}
_PREVIEW_TTL_SECONDS = 900  # 15 minutes


def _check_preview_done(current_user_id: UUID) -> None:
    key = str(current_user_id)
    last = _user_preview_at.get(key)
    if last is None or (time.time() - last) > _PREVIEW_TTL_SECONDS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe realizar una vista previa (/preview) antes de enviar mensajes",
        )


@router.post("/preview", response_model=PreviewResponse, dependencies=[Depends(require_permission("comunicacion:enviar"))])
async def preview_mensaje(
    data: PreviewRequest,
    session: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> PreviewResponse:
    """Render message preview without persisting. Requires comunicacion:enviar."""
    svc = PreviewService()
    result = await svc.preview(data.asunto, data.cuerpo, data.destinatario)
    # Mark preview done for this user (RN-16)
    _user_preview_at[str(current_user.id)] = time.time()
    return PreviewResponse(**result)


@router.post("", response_model=list[ComunicacionResponse], status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("comunicacion:enviar"))])
async def enqueue_mensajes(
    data: list[ComunicacionCreate],
    session: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> list[ComunicacionResponse]:
    """Enqueue one or more messages. If recipient count exceeds threshold, requires approval."""

    _check_preview_done(current_user.id)

    approval_svc = ApprovalService(session, current_user.tenant_id)
    requires_approval = await approval_svc.requires_approval(len(data))

    lote_id = uuid4() if requires_approval else None

    repo = ComunicacionRepository(session, current_user.tenant_id)
    created = []
    for item in data:
        obj = Comunicacion(
            tenant_id=current_user.tenant_id,
            asunto=item.asunto,
            cuerpo=item.cuerpo,
            destinatario=item.destinatario,
            estado=ComunicacionEstado.PENDIENTE,
            lote_id=lote_id,
        )
        created_obj = await repo.create(obj)
        created.append(created_obj)

    await session.commit()

    await audit_emit(
        session,
        AUDIT_COMUNICACION_ENVIAR,
        entity="comunicacion",
        tenant_id=current_user.tenant_id,
        detalle={
            "action": "enqueue",
            "count": len(created),
            "lote_id": str(lote_id) if lote_id else None,
            "requires_approval": requires_approval,
        },
    )

    return [
        ComunicacionResponse(
            id=c.id,
            tenant_id=c.tenant_id,
            asunto=c.asunto,
            cuerpo=c.cuerpo,
            destinatario=c.destinatario,
            estado=c.estado,
            lote_id=c.lote_id,
            error_detail=c.error_detail,
            enviado_at=c.enviado_at,
            retry_count=c.retry_count,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in created
    ]


@router.get("/lotes/{lote_id}", response_model=LoteStatusResponse, dependencies=[Depends(require_permission("comunicacion:enviar"))])
async def get_lote_status(
    lote_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> LoteStatusResponse:
    """Get status summary of all messages in a lote."""
    repo = ComunicacionRepository(session, current_user.tenant_id)
    counts = await repo.count_by_lote_and_estado(lote_id)
    total = sum(counts.values())
    return LoteStatusResponse(
        lote_id=lote_id,
        tenant_id=current_user.tenant_id,
        total=total,
        pendientes=counts.get(ComunicacionEstado.PENDIENTE, 0),
        enviando=counts.get(ComunicacionEstado.ENVIANDO, 0),
        enviados=counts.get(ComunicacionEstado.ENVIADO, 0),
        errores=counts.get(ComunicacionEstado.ERROR, 0),
        cancelados=counts.get(ComunicacionEstado.CANCELADO, 0),
    )


@router.post("/lotes/{lote_id}/aprobar", status_code=status.HTTP_200_OK, dependencies=[Depends(require_permission("comunicacion:aprobar"))])
async def approve_lote(
    lote_id: UUID,
    data: LoteAprobarRequest,
    session: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> LoteStatusResponse:
    """Approve a lote — transitions all Pendiente messages to Enviando for worker processing."""

    repo = ComunicacionRepository(session, current_user.tenant_id)
    messages = await repo.get_by_lote_id(lote_id)

    if not messages:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote no encontrado")

    pendiente_msgs = [m for m in messages if m.estado == ComunicacionEstado.PENDIENTE]
    if not pendiente_msgs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay mensajes pendientes en este lote",
        )

    for msg in pendiente_msgs:
        msg.transition_to(ComunicacionEstado.ENVIANDO)
        await session.flush()
        await audit_emit(
            session,
            AUDIT_COMUNICACION_APROBAR,
            entity="comunicacion",
            entity_id=msg.id,
            tenant_id=current_user.tenant_id,
            detalle={"from": "Pendiente", "to": "Enviando", "lote_id": str(lote_id)},
        )

    await session.commit()
    counts = await repo.count_by_lote_and_estado(lote_id)
    total = sum(counts.values())
    return LoteStatusResponse(
        lote_id=lote_id,
        tenant_id=current_user.tenant_id,
        total=total,
        pendientes=counts.get(ComunicacionEstado.PENDIENTE, 0),
        enviando=counts.get(ComunicacionEstado.ENVIANDO, 0),
        enviados=counts.get(ComunicacionEstado.ENVIADO, 0),
        errores=counts.get(ComunicacionEstado.ERROR, 0),
        cancelados=counts.get(ComunicacionEstado.CANCELADO, 0),
    )


@router.post("/lotes/{lote_id}/rechazar", status_code=status.HTTP_200_OK, dependencies=[Depends(require_permission("comunicacion:aprobar"))])
async def reject_lote(
    lote_id: UUID,
    data: LoteRechazarRequest,
    session: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> LoteStatusResponse:
    """Reject a lote — cancels all Pendiente messages."""

    repo = ComunicacionRepository(session, current_user.tenant_id)
    messages = await repo.get_by_lote_id(lote_id)

    if not messages:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote no encontrado")

    await repo.bulk_cancel(lote_id, data.razon)

    for msg in messages:
        await audit_emit(
            session,
            AUDIT_COMUNICACION_ENVIAR,
            entity="comunicacion",
            entity_id=msg.id,
            tenant_id=current_user.tenant_id,
            detalle={"from": str(msg.estado.value), "to": "Cancelado", "lote_id": str(lote_id)},
        )

    await session.commit()
    counts = await repo.count_by_lote_and_estado(lote_id)
    total = sum(counts.values())
    return LoteStatusResponse(
        lote_id=lote_id,
        tenant_id=current_user.tenant_id,
        total=total,
        pendientes=counts.get(ComunicacionEstado.PENDIENTE, 0),
        enviando=counts.get(ComunicacionEstado.ENVIANDO, 0),
        enviados=counts.get(ComunicacionEstado.ENVIADO, 0),
        errores=counts.get(ComunicacionEstado.ERROR, 0),
        cancelados=counts.get(ComunicacionEstado.CANCELADO, 0),
    )


@router.get("/{comunicacion_id}", response_model=ComunicacionResponse, dependencies=[Depends(require_permission("comunicacion:enviar"))])
async def get_mensaje(
    comunicacion_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> ComunicacionResponse:
    """Get a single message by ID."""
    repo = ComunicacionRepository(session, current_user.tenant_id)
    obj = await repo.get_by_id(comunicacion_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mensaje no encontrado")
    return ComunicacionResponse(
        id=obj.id,
        tenant_id=obj.tenant_id,
        asunto=obj.asunto,
        cuerpo=obj.cuerpo,
        destinatario=obj.destinatario,
        estado=obj.estado,
        lote_id=obj.lote_id,
        error_detail=obj.error_detail,
        enviado_at=obj.enviado_at,
        retry_count=obj.retry_count,
        created_at=obj.created_at,
        updated_at=obj.updated_at,
    )