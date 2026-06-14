from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mensaje_interno import MensajeInterno
from app.models.usuario import Usuario
from app.repositories.base import TenantScopedRepository


class InboxThreadItem:
    """A summary row for one thread in the inbox view."""

    def __init__(
        self,
        hilo_id: UUID,
        remitente_id: UUID,
        destinatario_id: UUID,
        ultimo_asunto: str,
        ultimo_cuerpo: str,
        leido: bool,
        ultima_actividad: datetime,
    ) -> None:
        self.hilo_id = hilo_id
        self.remitente_id = remitente_id
        self.destinatario_id = destinatario_id
        self.ultimo_asunto = ultimo_asunto
        self.ultimo_cuerpo = ultimo_cuerpo
        self.leido = leido
        self.ultima_actividad = ultima_actividad


class MensajeInternoRepository(TenantScopedRepository[MensajeInterno]):
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        super().__init__(session, MensajeInterno, tenant_id)

    async def list_inbox_threads(
        self, user_id: UUID
    ) -> list[InboxThreadItem]:
        """Return thread summaries where the user is sender or recipient."""
        subq = (
            select(
                MensajeInterno.hilo_id,
                func.max(MensajeInterno.created_at).label("ultima_actividad"),
            )
            .where(
                MensajeInterno.tenant_id == self._tenant_id,
                MensajeInterno.deleted_at.is_(None),
                (MensajeInterno.remitente_id == user_id)
                | (MensajeInterno.destinatario_id == user_id),
            )
            .group_by(MensajeInterno.hilo_id)
            .subquery()
        )

        latest = (
            select(MensajeInterno)
            .distinct(MensajeInterno.hilo_id)
            .where(
                MensajeInterno.tenant_id == self._tenant_id,
                MensajeInterno.deleted_at.is_(None),
                MensajeInterno.hilo_id == subq.c.hilo_id,
                MensajeInterno.created_at == subq.c.ultima_actividad,
            )
            .order_by(MensajeInterno.hilo_id, MensajeInterno.created_at.desc())
            .subquery()
        )

        stmt = (
            select(
                latest.c.hilo_id,
                latest.c.remitente_id,
                latest.c.destinatario_id,
                latest.c.asunto,
                latest.c.cuerpo,
                latest.c.leido_at,
                latest.c.created_at,
            )
            .where(latest.c.tenant_id == self._tenant_id)
            .order_by(latest.c.created_at.desc())
        )

        result = await self._session.execute(stmt)
        rows = []
        for row in result:
            rows.append(InboxThreadItem(
                hilo_id=row.hilo_id,
                remitente_id=row.remitente_id,
                destinatario_id=row.destinatario_id,
                ultimo_asunto=row.asunto,
                ultimo_cuerpo=row.cuerpo,
                leido=row.leido_at is not None,
                ultima_actividad=row.created_at,
            ))
        return rows

    async def get_thread_messages(self, hilo_id: UUID) -> list[MensajeInterno]:
        stmt = (
            select(MensajeInterno)
            .where(
                MensajeInterno.tenant_id == self._tenant_id,
                MensajeInterno.deleted_at.is_(None),
                MensajeInterno.hilo_id == hilo_id,
            )
            .order_by(MensajeInterno.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, id: UUID) -> MensajeInterno | None:
        stmt = (
            select(MensajeInterno)
            .where(
                MensajeInterno.id == id,
                MensajeInterno.tenant_id == self._tenant_id,
                MensajeInterno.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> MensajeInterno:
        if "tenant_id" not in data:
            data["tenant_id"] = self._tenant_id
        return await super().create(data)

    async def mark_as_read(
        self, hilo_id: UUID, destinatario_id: UUID
    ) -> None:
        now = datetime.now(timezone.utc)
        stmt = (
            update(MensajeInterno)
            .where(
                MensajeInterno.tenant_id == self._tenant_id,
                MensajeInterno.deleted_at.is_(None),
                MensajeInterno.hilo_id == hilo_id,
                MensajeInterno.destinatario_id == destinatario_id,
                MensajeInterno.leido_at.is_(None),
            )
            .values(leido_at=now)
        )
        await self._session.execute(stmt)

    async def find_usuario_in_tenant(
        self, usuario_id: UUID
    ) -> bool:
        stmt = (
            select(Usuario)
            .where(
                Usuario.id == usuario_id,
                Usuario.tenant_id == self._tenant_id,
                Usuario.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None
