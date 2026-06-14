from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.mensajes import (
    InboxThreadItem,
    MensajeCreate,
    MensajeReply,
    MensajeResponse,
)
from app.repositories.mensajes import MensajeInternoRepository


class MensajeService:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    def _repo(self) -> MensajeInternoRepository:
        return MensajeInternoRepository(self._session, self._tenant_id)

    async def send(self, data: MensajeCreate, remitente_id: UUID) -> MensajeResponse:
        repo = self._repo()

        exists = await repo.find_usuario_in_tenant(data.destinatario_id)
        if not exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Destinatario no encontrado",
            )

        msg_id = uuid4()
        hilo_id = data.hilo_id or msg_id

        obj = await repo.create({
            "id": msg_id,
            "tenant_id": self._tenant_id,
            "asunto": data.asunto,
            "cuerpo": data.cuerpo,
            "remitente_id": remitente_id,
            "destinatario_id": data.destinatario_id,
            "hilo_id": hilo_id,
            "padre_id": None,
        })
        return self._to_response(obj)

    async def reply(
        self, parent_id: UUID, data: MensajeReply, remitente_id: UUID
    ) -> MensajeResponse:
        repo = self._repo()

        parent = await repo.get_by_id(parent_id)
        if parent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mensaje original no encontrado",
            )

        destinatario_id = (
            parent.remitente_id
            if parent.destinatario_id == remitente_id
            else parent.destinatario_id
        )

        obj = await repo.create({
            "tenant_id": self._tenant_id,
            "asunto": data.asunto,
            "cuerpo": data.cuerpo,
            "remitente_id": remitente_id,
            "destinatario_id": destinatario_id,
            "hilo_id": parent.hilo_id,
            "padre_id": parent.id,
        })
        return self._to_response(obj)

    async def list_inbox(self, user_id: UUID) -> list[InboxThreadItem]:
        repo = self._repo()
        threads = await repo.list_inbox_threads(user_id)
        return [
            InboxThreadItem(
                hilo_id=t.hilo_id,
                remitente_id=t.remitente_id,
                destinatario_id=t.destinatario_id,
                ultimo_asunto=t.ultimo_asunto,
                ultimo_cuerpo=t.ultimo_cuerpo,
                leido=t.leido,
                ultima_actividad=t.ultima_actividad,
            )
            for t in threads
        ]

    async def read_thread(
        self, hilo_id: UUID, user_id: UUID
    ) -> list[MensajeResponse]:
        repo = self._repo()
        messages = await repo.get_thread_messages(hilo_id)

        if not messages:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hilo no encontrado",
            )

        user_in_thread = any(
            m.remitente_id == user_id or m.destinatario_id == user_id
            for m in messages
        )
        if not user_in_thread:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hilo no encontrado",
            )

        await repo.mark_as_read(hilo_id, user_id)
        await self._session.flush()

        # Re-fetch to avoid expired-attribute (MissingGreenlet) on the bulk-updated rows
        messages = await repo.get_thread_messages(hilo_id)
        return [self._to_response(m) for m in messages]

    def _to_response(self, obj) -> MensajeResponse:
        return MensajeResponse(
            id=obj.id,
            tenant_id=obj.tenant_id,
            asunto=obj.asunto,
            cuerpo=obj.cuerpo,
            remitente_id=obj.remitente_id,
            destinatario_id=obj.destinatario_id,
            hilo_id=obj.hilo_id,
            padre_id=obj.padre_id,
            leido_at=obj.leido_at,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )
