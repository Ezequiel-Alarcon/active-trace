from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

# TODO: (FEAT) Agregar permisos mensajes:enviar y mensajes:ver al catálogo y
# decorar estos endpoints con require_permission para mantener consistencia
# con el resto del codebase.
from app.auth.deps import CurrentUser, get_current_user
from app.core.dependencies import get_db
from app.schemas.mensajes import (
    InboxThreadItem,
    MensajeCreate,
    MensajeReply,
    MensajeResponse,
)
from app.services.mensajes import MensajeService

router = APIRouter(prefix="/api/mensajes", tags=["mensajes"])


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
)
async def read_thread(
    hilo_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[MensajeService, Depends(_get_service)],
):
    return await service.read_thread(hilo_id, current_user.user_id)
