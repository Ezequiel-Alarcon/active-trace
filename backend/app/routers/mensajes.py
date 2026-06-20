from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_user
from app.core.dependencies import get_db
from app.core.permissions import require_permission
from app.schemas.mensajes import (
    InboxThreadItem,
    MensajeCreate,
    MensajeReply,
    MensajeResponse,
)
from app.services.mensajes import MensajeService

router = APIRouter(prefix="/api/mensajes", tags=["mensajes"])

# TODO: (REVIEW) Auditoría backend/frontend 2026-06-19: C-20/CHANGES documenta
# `/api/inbox/*`, pero el backend expone `/api/mensajes/inbox*`. La
# funcionalidad existe, pero el contrato documentado no coincide.


def _get_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> MensajeService:
    return MensajeService(db, current_user.tenant_id)


@router.post(
    "/",
    response_model=MensajeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send a new internal message",
    dependencies=[Depends(require_permission("mensajes:enviar"))],
)
async def send_message(
    data: MensajeCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[MensajeService, Depends(_get_service)],
):
    return await service.send(data, current_user.user_id)


@router.post(
    "/{mensaje_id}/reply",
    response_model=MensajeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Reply to an existing message",
    dependencies=[Depends(require_permission("mensajes:enviar"))],
)
async def reply_message(
    mensaje_id: UUID,
    data: MensajeReply,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[MensajeService, Depends(_get_service)],
):
    return await service.reply(mensaje_id, data, current_user.user_id)


@router.get(
    "/inbox",
    response_model=list[InboxThreadItem],
    summary="List inbox threads",
    dependencies=[Depends(require_permission("mensajes:ver"))],
)
async def list_inbox(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[MensajeService, Depends(_get_service)],
):
    return await service.list_inbox(current_user.user_id)


@router.get(
    "/inbox/{hilo_id}",
    response_model=list[MensajeResponse],
    summary="Read thread messages",
    dependencies=[Depends(require_permission("mensajes:ver"))],
)
async def read_thread(
    hilo_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[MensajeService, Depends(_get_service)],
):
    return await service.read_thread(hilo_id, current_user.user_id)
